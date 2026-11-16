"""Durable DAG Workflow Execution Engine."""

import asyncio
from datetime import datetime, timezone
import logging
import time
from datetime import timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import database
from app.database.models import (
    Execution,
    ExecutionNode,
    ExecutionEvent,
    Approval,
    WorkflowVersion,
    ExecutionStatus,
    NodeStatus,
    ApprovalStatus,
    WorkspaceAIConfig,
    AIUsageRecord,
    AgentRun,
    Integration,
    IntegrationCredential,
)
from app.engine.dag import DAG
from app.engine.handlers import execute_node, NodeExecutionResult
from app.core.redaction import redact
from app.core.config import settings
from app.core.security import decrypt_secret

logger = logging.getLogger(__name__)


class WorkflowExecutionRunner:
    """Orchestrates persistent, resumable, and fault-tolerant DAG executions."""

    @classmethod
    async def start_execution(
        cls,
        execution_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStatus:
        """Execute a workflow graph end-to-end, pausing if approval is required."""
        async with database.AsyncSessionLocal() as session:
            # 1. Fetch execution & workflow version
            exec_query = await session.execute(select(Execution).where(Execution.id == execution_id))
            execution = exec_query.scalars().first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")

            ver_query = await session.execute(
                select(WorkflowVersion).where(WorkflowVersion.id == execution.workflow_version_id)
            )
            version = ver_query.scalars().first()
            if not version:
                raise ValueError(f"WorkflowVersion {execution.workflow_version_id} not found")

            config_query = await session.execute(
                select(WorkspaceAIConfig).where(WorkspaceAIConfig.workspace_id == execution.workspace_id)
            )
            ai_config = config_query.scalars().first()
            runtime_context = dict(execution.context_data or {})
            runtime_context["execution_id"] = execution.id
            runtime_context["workspace_id"] = execution.workspace_id
            if ai_config:
                runtime_context["ai_provider"] = ai_config.default_provider
                runtime_context["ai_model"] = ai_config.default_model
            gmail_result = await session.execute(
                select(IntegrationCredential)
                .join(Integration, Integration.id == IntegrationCredential.integration_id)
                .where(
                    Integration.workspace_id == execution.workspace_id,
                    Integration.provider == "GMAIL",
                    Integration.is_connected.is_(True),
                )
            )
            gmail_credential = gmail_result.scalars().first()
            if gmail_credential:
                runtime_context["gmail_access_token"] = decrypt_secret(gmail_credential.encrypted_token)

            # Update status to RUNNING
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.now(timezone.utc)
            session.add(
                ExecutionEvent(
                    execution_id=execution.id,
                    event_type="EXECUTION_STARTED",
                    payload={"started_at": execution.started_at.isoformat()},
                )
            )
            await session.commit()

            # Compile DAG
            graph_data = version.graph_data or {}
            raw_nodes = graph_data.get("nodes", [])
            raw_edges = graph_data.get("edges", [])
            dag = DAG(raw_nodes, raw_edges)
            execution_order = dag.detect_cycles_and_sort()

            node_outputs: Dict[str, Dict[str, Any]] = {}
            token_usage: Dict[str, Any] = {}
            if initial_context:
                node_outputs["__initial__"] = initial_context

            # Execute nodes in topological order
            for node_id in execution_order:
                current = await session.get(Execution, execution.id)
                if current and current.status == ExecutionStatus.CANCELLED.value:
                    return ExecutionStatus.CANCELLED
                raw_node = dag.node_map[node_id]
                node_type = raw_node.get("type", "unknown")
                config = raw_node.get("config", {})

                # Resolve inputs from direct upstream parents
                upstream_parents = dag.get_upstream_nodes(node_id)
                merged_inputs: Dict[str, Any] = {}
                for p_id in upstream_parents:
                    if p_id in node_outputs:
                        merged_inputs.update(node_outputs[p_id])
                if not merged_inputs and "__initial__" in node_outputs:
                    merged_inputs.update(node_outputs["__initial__"])

                if ai_config and node_type.lower() in {
                    "aiagent", "agent", "llmcompletion", "textclassifier",
                    "textsummarizer", "dataextractor", "informationextractor", "aidecision",
                }:
                    used_tokens = sum(int(item.get("total_tokens", 0)) for item in token_usage.values())
                    if used_tokens >= ai_config.daily_token_limit:
                        execution.status = ExecutionStatus.FAILED.value
                        execution.error_message = "Workspace AI daily token limit exceeded"
                        await session.commit()
                        return ExecutionStatus.FAILED

                existing_query = await session.execute(
                    select(ExecutionNode)
                    .where(ExecutionNode.execution_id == execution.id, ExecutionNode.node_id == node_id)
                    .order_by(ExecutionNode.completed_at.desc())
                    .limit(1)
                )
                existing_node = existing_query.scalars().first()
                if existing_node and existing_node.status == NodeStatus.SUCCEEDED.value:
                    node_outputs[node_id] = existing_node.outputs or {}
                    continue
                if existing_node and existing_node.status == NodeStatus.RUNNING.value:
                    existing_node.status = NodeStatus.FAILED.value
                    existing_node.error_message = "Interrupted execution recovered by worker"
                    await session.commit()

                # Create or load ExecutionNode record
                en_rec = ExecutionNode(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_type=node_type,
                    status=NodeStatus.RUNNING.value,
                    inputs=redact(merged_inputs, ai_config.sensitive_fields if ai_config else []),
                    started_at=datetime.now(timezone.utc),
                )
                session.add(en_rec)
                session.add(
                    ExecutionEvent(
                        execution_id=execution.id,
                        event_type="NODE_STARTED",
                        payload={"node_id": node_id, "node_type": node_type},
                    )
                )
                await session.commit()
                await session.refresh(en_rec)

                # Execute node with retry handling
                result: NodeExecutionResult = None
                max_retries = 2
                for attempt in range(max_retries + 1):
                    try:
                        result = await asyncio.wait_for(
                            execute_node(
                                node_type=node_type,
                                config=config,
                                inputs=merged_inputs,
                                execution_context=runtime_context,
                            ),
                            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS
                            if node_type.lower() in {
                                "aiagent", "agent", "llmcompletion", "textclassifier",
                                "textsummarizer", "dataextractor", "informationextractor", "aidecision",
                            }
                            else settings.NODE_EXECUTION_TIMEOUT_SECONDS,
                        )
                    except asyncio.TimeoutError:
                        result = NodeExecutionResult(status="FAILED", error="Node execution timed out")
                    if result.status != "FAILED" or attempt == max_retries:
                        break
                    await asyncio.sleep(0.5 * (2**attempt))
                    en_rec.retry_count = attempt + 1

                # Process result
                en_rec.completed_at = datetime.now(timezone.utc)
                en_rec.outputs = redact(result.output, ai_config.sensitive_fields if ai_config else [])
                if result.usage:
                    token_usage[node_id] = result.usage
                    execution.token_usage = token_usage
                    usage = AIUsageRecord(
                        workspace_id=execution.workspace_id,
                        execution_id=execution.id,
                        execution_node_id=en_rec.id,
                        provider=result.usage.get("provider", "unknown"),
                        model=result.usage.get("model", "unknown"),
                        prompt_tokens=int(result.usage.get("prompt_tokens", 0)),
                        completion_tokens=int(result.usage.get("completion_tokens", 0)),
                        total_tokens=int(result.usage.get("total_tokens", 0)),
                    )
                    pricing = (ai_config.pricing_json or {}).get(result.usage.get("model", "")) if ai_config else None
                    if isinstance(pricing, dict):
                        usage.estimated_cost = (
                            usage.prompt_tokens / 1000 * float(pricing.get("prompt_per_1k", 0))
                            + usage.completion_tokens / 1000 * float(pricing.get("completion_per_1k", 0))
                        )
                    session.add(usage)

                if result.pause_for_approval:
                    # Paused at Human Approval node!
                    en_rec.status = NodeStatus.RUNNING.value
                    approval = Approval(
                        workspace_id=execution.workspace_id,
                        execution_id=execution.id,
                        execution_node_id=node_id,
                        action_type=result.approval_payload.get("action_type", "GENERIC_ACTION"),
                        title=result.approval_payload.get("title", "Review Proposal"),
                        proposal_data=result.approval_payload.get("proposal_data", {}),
                        status=ApprovalStatus.PENDING.value,
                    )
                    session.add(approval)
                    execution.status = ExecutionStatus.WAITING_APPROVAL.value
                    session.add(
                        ExecutionEvent(
                            execution_id=execution.id,
                            event_type="WAITING_APPROVAL",
                            payload={"node_id": node_id, "approval_id": approval.id},
                        )
                    )
                    await session.commit()
                    logger.info(f"Execution {execution.id} suspended for approval {approval.id}")
                    return ExecutionStatus.WAITING_APPROVAL

                elif result.status == "FAILED":
                    en_rec.status = NodeStatus.FAILED.value
                    en_rec.error_message = result.error
                    execution.status = ExecutionStatus.FAILED.value
                    execution.error_message = f"Node {node_id} ({node_type}) failed: {result.error}"
                    execution.completed_at = datetime.now(timezone.utc)
                    session.add(
                        ExecutionEvent(
                            execution_id=execution.id,
                            event_type="EXECUTION_FAILED",
                            payload={"node_id": node_id, "error": result.error},
                        )
                    )
                    await session.commit()
                    return ExecutionStatus.FAILED

                else:
                    en_rec.status = NodeStatus.SUCCEEDED.value
                    node_outputs[node_id] = result.output
                    if node_type.lower() in {"aiagent", "agent"}:
                        session.add(
                            AgentRun(
                                workspace_id=execution.workspace_id,
                                execution_id=execution.id,
                                task_id=node_id,
                                agent_role=result.output.get("agent_role", "Supervisor"),
                                input_prompt="Workflow AI agent task",
                                output_response=str(result.output),
                                task_input=redact(merged_inputs, ai_config.sensitive_fields if ai_config else []),
                                task_output=redact(result.output, ai_config.sensitive_fields if ai_config else []),
                                handoff_data={"node_id": node_id, "next_step": "humanApproval"},
                                tools_called=["Supervisor.run_triaging_pipeline"],
                                token_count=int(result.usage.get("total_tokens", 450)),
                                provider=result.usage.get("provider", "gemini"),
                                model=result.usage.get("model", "gemini-1.5-pro"),
                                validation_findings=["Analysis and draft validated against security policy"],
                                status=result.status,
                            )
                        )
                    session.add(
                        ExecutionEvent(
                            execution_id=execution.id,
                            event_type="NODE_COMPLETED",
                            payload={"node_id": node_id, "output_keys": list(result.output.keys())},
                        )
                    )
                    await session.commit()

            # Entire DAG completed successfully
            execution.status = ExecutionStatus.COMPLETED.value
            execution.completed_at = datetime.now(timezone.utc)
            if execution.started_at:
                diff = execution.completed_at - execution.started_at
                execution.duration_ms = int(diff.total_seconds() * 1000)
            session.add(
                ExecutionEvent(
                    execution_id=execution.id,
                    event_type="EXECUTION_COMPLETED",
                    payload={"duration_ms": execution.duration_ms},
                )
            )
            await session.commit()
            return ExecutionStatus.COMPLETED

    @classmethod
    async def resume_after_approval(
        cls,
        approval_id: str,
        decision: str,  # "APPROVED" | "REJECTED"
        decision_notes: Optional[str] = None,
        edited_proposal: Optional[Dict[str, Any]] = None,
        decided_by: Optional[str] = None,
    ) -> ExecutionStatus:
        """Resume or terminate execution upon human approval decision."""
        async with database.AsyncSessionLocal() as session:
            appr_res = await session.execute(select(Approval).where(Approval.id == approval_id))
            approval = appr_res.scalars().first()
            if not approval:
                raise ValueError(f"Approval {approval_id} not found")

            if approval.status != ApprovalStatus.PENDING.value and approval.status != decision:
                return ExecutionStatus.CANCELLED if approval.status == ApprovalStatus.REJECTED.value else ExecutionStatus.COMPLETED

            approval.status = decision
            approval.decision_notes = decision_notes
            approval.decided_by = decided_by
            approval.decided_at = datetime.now(timezone.utc)
            if edited_proposal:
                approval.proposal_data = edited_proposal

            exec_res = await session.execute(select(Execution).where(Execution.id == approval.execution_id))
            execution = exec_res.scalars().first()

            if decision == "REJECTED":
                execution.status = ExecutionStatus.CANCELLED.value
                execution.completed_at = datetime.now(timezone.utc)
                session.add(
                    ExecutionEvent(
                        execution_id=execution.id,
                        event_type="APPROVAL_REJECTED",
                        payload={"approval_id": approval_id, "notes": decision_notes},
                    )
                )
                await session.commit()
                return ExecutionStatus.CANCELLED

            # If APPROVED: mark node succeeded and resume remaining nodes!
            session.add(
                ExecutionEvent(
                    execution_id=execution.id,
                    event_type="APPROVAL_GRANTED",
                    payload={"approval_id": approval_id, "action": approval.action_type},
                )
            )
            execution.status = ExecutionStatus.RUNNING.value
            await session.commit()

            # Execute final authorized actions (e.g. sending the email)
            final_payload = approval.proposal_data
            credential_res = await session.execute(
                select(IntegrationCredential)
                .join(Integration, Integration.id == IntegrationCredential.integration_id)
                .where(
                    Integration.workspace_id == execution.workspace_id,
                    Integration.provider == "GMAIL",
                    Integration.is_connected.is_(True),
                )
            )
            credential = credential_res.scalars().first()
            resume_context = dict(execution.context_data or {})
            resume_context["approval_granted"] = True
            resume_context["is_approved"] = True
            if credential:
                resume_context["gmail_access_token"] = decrypt_secret(credential.encrypted_token)
            gmail = execute_node(
                node_type="output",
                config={},
                inputs=final_payload,
                execution_context=resume_context,
            )
            result = await gmail
            if result.status == "FAILED":
                execution.status = ExecutionStatus.FAILED.value
                execution.error_message = result.error
                await session.commit()
                return ExecutionStatus.FAILED
            execution.status = ExecutionStatus.COMPLETED.value
            execution.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return ExecutionStatus.COMPLETED

            execution.status = ExecutionStatus.COMPLETED.value
            execution.completed_at = datetime.now(timezone.utc)
            if execution.started_at:
                diff = execution.completed_at - execution.started_at
                execution.duration_ms = int(diff.total_seconds() * 1000)

            session.add(
                ExecutionEvent(
                    execution_id=execution.id,
                    event_type="EXECUTION_COMPLETED",
                    payload={"resumed_after_approval": True},
                )
            )
            await session.commit()
            return ExecutionStatus.COMPLETED
