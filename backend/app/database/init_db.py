"""Database initialization and schema migration bootstrap."""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import (
    async_engine,
    Base,
    AsyncSessionLocal,
    fallback_to_sqlite,
)
from app.core.security import hash_password
from app.database.models import (
    User,
    Workspace,
    WorkspaceMember,
    RoleEnum,
    Workflow,
    WorkflowVersion,
    WorkflowNode,
    Execution,
    ExecutionNode,
    Approval,
    AuditLog,
    ExecutionStatus,
    NodeStatus,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)


def _sync_upgrade_columns(sync_conn):
    from sqlalchemy import inspect, text
    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()
    if "agent_runs" in tables:
        columns = [col["name"] for col in inspector.get_columns("agent_runs")]
        new_cols = [
            ("provider", "VARCHAR(50)"),
            ("model", "VARCHAR(150)"),
            ("error_message", "TEXT"),
            ("validation_findings", "JSON"),
            ("approval_status", "VARCHAR(30)"),
            ("idempotency_key", "VARCHAR(128)"),
        ]
        for col_name, col_type in new_cols:
            if col_name not in columns:
                try:
                    sync_conn.execute(text(f"ALTER TABLE agent_runs ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"Added column {col_name} to agent_runs table")
                except Exception as exc:
                    logger.debug(f"Could not add column {col_name} to agent_runs: {exc}")


async def init_db():
    """Create all tables in the configured database with automatic fallback."""
    global async_engine, AsyncSessionLocal
    import app.core.database as db_mod

    try:
        async with db_mod.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_sync_upgrade_columns)
        logger.info("Database tables initialized successfully via primary engine.")
    except Exception as e:
        logger.warning(f"Failed to connect to primary database ({e}). Engaging SQLite fallback.")
        db_mod.fallback_to_sqlite()
        async with db_mod.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_sync_upgrade_columns)
        logger.info("Database tables initialized successfully via SQLite fallback.")

    # Seed demo account and workspace if empty
    async with db_mod.AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalars().first()

        if not existing_user:
            demo_user = User(
                email="demo@flowpilot.ai",
                password_hash=hash_password("FlowPilot2026!"),
                full_name="Alex Mercer (Demo)",
                is_active=True,
                is_superuser=True,
            )
            session.add(demo_user)
            await session.flush()

            demo_workspace = Workspace(
                name="Acme Autonomous Ops",
                slug="acme-ops",
                owner_id=demo_user.id,
            )
            session.add(demo_workspace)
            await session.flush()

            membership = WorkspaceMember(
                workspace_id=demo_workspace.id,
                user_id=demo_user.id,
                role=RoleEnum.OWNER.value,
            )
            session.add(membership)
            await session.commit()
            logger.info("Demo user and workspace seeded: demo@flowpilot.ai / FlowPilot2026!")

        # Ensure demo workspace and workflow exists
        ws_res = await session.execute(select(Workspace).limit(1))
        active_ws = ws_res.scalars().first()

        if active_ws:
            wf_res = await session.execute(select(Workflow).where(Workflow.workspace_id == active_ws.id).limit(1))
            active_wf = wf_res.scalars().first()

            if not active_wf:
                graph_data = {
                    "nodes": [
                        {"id": "node-1", "type": "gmailTrigger", "label": "Gmail: Fetch Unread", "position": {"x": 100, "y": 180}, "config": {"folder": "INBOX"}},
                        {"id": "node-2", "type": "textClassifier", "label": "AI Analyst: Classify Urgency", "position": {"x": 420, "y": 180}, "config": {}},
                        {"id": "node-3", "type": "aiAgent", "label": "AI Drafter: Draft Response", "position": {"x": 740, "y": 180}, "config": {}},
                        {"id": "node-4", "type": "humanApproval", "label": "Human Approval: Review Draft", "position": {"x": 1060, "y": 180}, "config": {"action": "SEND_GMAIL_MESSAGE"}},
                        {"id": "node-5", "type": "output", "label": "Dispatch Approved Email", "position": {"x": 1380, "y": 180}, "config": {}},
                    ],
                    "edges": [
                        {"id": "e1-2", "source": "node-1", "target": "node-2"},
                        {"id": "e2-3", "source": "node-2", "target": "node-3"},
                        {"id": "e3-4", "source": "node-3", "target": "node-4"},
                        {"id": "e4-5", "source": "node-4", "target": "node-5"},
                    ],
                }
                active_wf = Workflow(
                    workspace_id=active_ws.id,
                    name="Autonomous Gmail Triaging & Draft",
                    description="Reads unread emails, classifies urgency, drafts response, and awaits human authorization.",
                    is_active=True,
                )
                session.add(active_wf)
                await session.flush()

                wf_ver = WorkflowVersion(
                    workflow_id=active_wf.id,
                    version_number=1,
                    graph_data=graph_data,
                    is_published=True,
                    changelog="Initial baseline version",
                )
                session.add(wf_ver)
                await session.flush()

                active_wf.current_version_id = wf_ver.id
                await session.commit()
                logger.info("Demo workflow seeded.")

            # Ensure demo executions and pending approval exist
            exc_res = await session.execute(select(Execution).where(Execution.workspace_id == active_ws.id).limit(1))
            existing_exc = exc_res.scalars().first()

            if not existing_exc and active_wf:
                # 1. Execution waiting for approval
                exc1 = Execution(
                    workspace_id=active_ws.id,
                    workflow_id=active_wf.id,
                    workflow_version_id=active_wf.current_version_id or "v1",
                    status=ExecutionStatus.WAITING_APPROVAL.value,
                    trigger_type="GMAIL_TRIGGER",
                    context_data={"unread_count": 1, "sender": "alex@enterprise.corp", "subject": "Urgent: Q4 Migration Review"},
                    duration_ms=1240,
                    token_usage={"prompt_tokens": 420, "completion_tokens": 180, "total_tokens": 600},
                )
                session.add(exc1)
                await session.flush()

                node1_1 = ExecutionNode(
                    execution_id=exc1.id,
                    node_id="node-1",
                    node_type="gmailTrigger",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"folder": "INBOX", "unread_only": True},
                    outputs={"emails_found": 1, "subject": "Urgent: Q4 Migration Review", "from": "alex@enterprise.corp"},
                )
                node1_2 = ExecutionNode(
                    execution_id=exc1.id,
                    node_id="node-2",
                    node_type="textClassifier",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"subject": "Urgent: Q4 Migration Review"},
                    outputs={"classification": "Urgent", "urgency_score": 0.96, "category": "Infrastructure"},
                )
                node1_3 = ExecutionNode(
                    execution_id=exc1.id,
                    node_id="node-3",
                    node_type="aiAgent",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"classification": "Urgent", "tone": "Professional"},
                    outputs={"draft_to": "alex@enterprise.corp", "draft_subject": "Re: Urgent: Q4 Migration Review", "draft_body": "Hi Alex,\n\nI reviewed the Q4 migration review deliverables. All validation tests have passed and we are ready for Friday deployment.\n\nBest regards,\nAlex Mercer (Demo Assistant)"},
                )
                node1_4 = ExecutionNode(
                    execution_id=exc1.id,
                    node_id="node-4",
                    node_type="humanApproval",
                    status=NodeStatus.RUNNING.value,
                    inputs={"action": "SEND_GMAIL_MESSAGE", "timeout_hours": 24},
                    outputs={"status": "AWAITING_USER_APPROVAL"},
                )
                session.add_all([node1_1, node1_2, node1_3, node1_4])
                await session.flush()

                appr1 = Approval(
                    workspace_id=active_ws.id,
                    execution_id=exc1.id,
                    execution_node_id="node-4",
                    action_type="SEND_GMAIL_MESSAGE",
                    title="Authorize Automated Email Dispatch",
                    proposal_data={
                        "to": "alex@enterprise.corp",
                        "subject": "Re: Urgent: Q4 Migration Review",
                        "draft_body": "Hi Alex,\n\nI reviewed the Q4 migration review deliverables. All validation tests have passed and we are ready for Friday deployment.\n\nBest regards,\nAlex Mercer (Demo Assistant)",
                    },
                    status=ApprovalStatus.PENDING.value,
                )
                session.add(appr1)

                # 2. Completed execution
                exc2 = Execution(
                    workspace_id=active_ws.id,
                    workflow_id=active_wf.id,
                    workflow_version_id=active_wf.current_version_id or "v1",
                    status=ExecutionStatus.COMPLETED.value,
                    trigger_type="MANUAL",
                    context_data={"source": "manual_trigger"},
                    duration_ms=450,
                    token_usage={"prompt_tokens": 250, "completion_tokens": 100, "total_tokens": 350},
                )
                session.add(exc2)
                await session.flush()

                node2_1 = ExecutionNode(
                    execution_id=exc2.id,
                    node_id="node-1",
                    node_type="gmailTrigger",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"folder": "INBOX"},
                    outputs={"processed": 3},
                )
                node2_2 = ExecutionNode(
                    execution_id=exc2.id,
                    node_id="node-2",
                    node_type="textClassifier",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"count": 3},
                    outputs={"triaged": 3},
                )
                node2_3 = ExecutionNode(
                    execution_id=exc2.id,
                    node_id="node-3",
                    node_type="aiAgent",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"triaged": 3},
                    outputs={"summarized": 3},
                )
                node2_4 = ExecutionNode(
                    execution_id=exc2.id,
                    node_id="node-5",
                    node_type="output",
                    status=NodeStatus.SUCCEEDED.value,
                    inputs={"status": "approved"},
                    outputs={"dispatched": 3},
                )
                session.add_all([node2_1, node2_2, node2_3, node2_4])
                await session.commit()
                logger.info("Demo executions and pending approval seeded successfully.")

        # Ensure demo audit logs exist
        if active_ws:
            audit_res = await session.execute(select(AuditLog).where(AuditLog.workspace_id == active_ws.id).limit(1))
            if not audit_res.scalars().first():
                seed_logs = [
                    AuditLog(
                        workspace_id=active_ws.id,
                        action="WORKSPACE_INITIALIZED",
                        resource_type="workspace",
                        resource_id=active_ws.id,
                        details={"tier": "Enterprise SaaS", "tenant": "acme-ops"},
                    ),
                    AuditLog(
                        workspace_id=active_ws.id,
                        action="AI_CONFIG_UPDATED",
                        resource_type="ai_config",
                        details={"default_provider": "gemini", "default_model": "gemini-1.5-pro"},
                    ),
                    AuditLog(
                        workspace_id=active_ws.id,
                        action="WORKFLOW_PUBLISHED",
                        resource_type="workflow",
                        details={"workflow_name": "Autonomous Gmail Triaging & Draft", "version": 1},
                    ),
                ]
                session.add_all(seed_logs)
                await session.commit()
                logger.info("Demo audit logs seeded.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
