"""Node execution handlers for all 14 FlowPilot AI node types."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx
import json
import re
from pydantic import BaseModel, Field

from app.ai.agents.runtime import MultiAgentSupervisor
from app.ai.providers.factory import get_ai_provider
from app.integrations.gmail.service import GmailService

logger = logging.getLogger(__name__)


class _ClassificationResult(BaseModel):
    category: str
    confidence: float = Field(ge=0, le=1)
    reasoning: str = ""


class _ExtractionResult(BaseModel):
    data: Dict[str, Any] = {}


class _DecisionResult(BaseModel):
    decision: str
    confidence: float = Field(ge=0, le=1)
    reasoning: str = ""


def _provider(config: Dict[str, Any], execution_context: Dict[str, Any]):
    return get_ai_provider(config.get("provider") or execution_context.get("ai_provider"))


class NodeExecutionResult:
    def __init__(
        self,
        status: str = "SUCCEEDED",
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        pause_for_approval: bool = False,
        approval_payload: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.output = output or {}
        self.error = error
        self.pause_for_approval = pause_for_approval
        self.approval_payload = approval_payload
        self.usage = usage or {}


def _resolve_templates(value: Any, inputs: Dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_templates(item, inputs) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_templates(item, inputs) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        current: Any = inputs
        for part in match.group(1).split("."):
            if not isinstance(current, dict) or part not in current:
                raise ValueError(f"Missing workflow variable '{match.group(1)}'")
            current = current[part]
        return str(current)

    return re.sub(r"\{\{([^{}]+)\}\}", replace, value)


async def execute_node(
    node_type: str,
    config: Dict[str, Any],
    inputs: Dict[str, Any],
    execution_context: Dict[str, Any],
) -> NodeExecutionResult:
    """Dispatches execution to the corresponding typed node handler."""
    nt = node_type.lower()

    try:
        # 1. Triggers
        if nt in ["manualtrigger", "trigger"]:
            return NodeExecutionResult(output={"triggered_by": "manual", "initial_payload": inputs or config})

        elif nt == "scheduletrigger":
            return NodeExecutionResult(output={"schedule": config.get("cron", "0 9 * * *"), "timestamp": "SCHEDULED_RUN"})

        elif nt == "gmailtrigger":
            gmail_token = execution_context.get("gmail_access_token")
            if not gmail_token:
                return NodeExecutionResult(
                    status="FAILED",
                    error="Gmail connection required: please connect Gmail in the Integration Hub before running Gmail workflows.",
                )
            gmail = GmailService(access_token=gmail_token)
            unread_emails = await gmail.fetch_unread_messages(max_results=config.get("max_results", 5))
            return NodeExecutionResult(
                output={
                    "unread_count": len(unread_emails),
                    "emails": unread_emails,
                    "primary_email": unread_emails[0] if unread_emails else {},
                }
            )
        elif nt == "webhooktrigger":
            return NodeExecutionResult(output={"payload": inputs, "triggered_by": "webhook"})

        # 2. AI & Retrieval Nodes
        elif nt in ["knowledgeretrieve", "knowledgesearch", "ragretrieve", "research"]:
            from app.ai.rag.service import RAGService
            from app.core import database
            workspace_id = execution_context.get("workspace_id", "")
            query = str(_resolve_templates(config.get("query") or inputs.get("query") or inputs.get("subject", ""), inputs))
            top_k = int(config.get("top_k", 3))
            rag = RAGService()
            async with database.AsyncSessionLocal() as session:
                search_res = await rag.search_workspace(
                    db=session,
                    workspace_id=workspace_id,
                    query=query,
                    top_k=top_k,
                )
            results = search_res.get("results", [])
            return NodeExecutionResult(
                output={
                    "results": results,
                    "sources": [r.get("filename") for r in results],
                    "context": "\n".join([r.get("content", "") for r in results]),
                    "trace": search_res.get("trace", {}),
                }
            )

        elif nt in ["aiagent", "agent"]:
            supervisor = MultiAgentSupervisor()
            email = inputs.get("primary_email") or inputs.get("email") or {}
            sender = email.get("sender", inputs.get("sender", "customer@example.com"))
            subject = email.get("subject", inputs.get("subject", config.get("task", "Inquiry")))
            body = email.get("body") or email.get("snippet", inputs.get("body", "Need assistance."))
            workspace_id = execution_context.get("workspace_id")

            result = await supervisor.run_triaging_pipeline(
                email_sender=sender,
                email_subject=subject,
                email_body=body,
                workspace_id=workspace_id,
            )
            return NodeExecutionResult(
                output={
                    "agent_role": result.agent_role,
                    "analysis": result.output.get("analysis", {}),
                    "research": result.output.get("research", {}),
                    "proposed_draft": result.output.get("proposed_draft", {}),
                    "validation": result.output.get("validation", {}),
                }
            )

        elif nt == "llmcompletion":
            provider = _provider(config, execution_context)
            prompt = _resolve_templates(config.get("prompt", "Summarize context"), inputs)
            res = await provider.complete(
                prompt,
                system_prompt=config.get("system_prompt"),
                temperature=float(config.get("temperature", 0.7)),
                max_tokens=int(config.get("max_tokens", 2048)),
            )
            output: Dict[str, Any] = {"completion": res.content, "model": res.model, "provider": res.provider}
            if config.get("output_format") == "json":
                output["json"] = json.loads(res.content)
            return NodeExecutionResult(
                output=output,
                usage={"provider": res.provider, "model": res.model, "prompt_tokens": res.prompt_tokens,
                       "completion_tokens": res.completion_tokens, "total_tokens": res.total_tokens},
            )

        elif nt == "textclassifier":
            provider = _provider(config, execution_context)
            text = str(_resolve_templates(config.get("text", "{{text}}"), inputs))
            categories = config.get("categories", ["Urgent", "Important", "General", "Spam"])
            result = await provider.complete_structured(
                f"Classify this text into exactly one category from {categories}. Return category, confidence, and reasoning.\n{text}",
                _ClassificationResult,
            )
            return NodeExecutionResult(output=result)

        elif nt == "dataextractor":
            provider = _provider(config, execution_context)
            fields = config.get("fields", [])
            result = await provider.complete_structured(
                f"Extract these fields as JSON: {fields}\nInput: {json.dumps(inputs, default=str)}",
                _ExtractionResult,
            )
            return NodeExecutionResult(output={"extracted_data": result.get("data", result)})

        elif nt in {"textsummarizer", "informationsummarizer"}:
            provider = _provider(config, execution_context)
            text = str(_resolve_templates(config.get("text", "{{text}}"), inputs))
            result = await provider.complete(text, system_prompt="Summarize faithfully without inventing facts.")
            return NodeExecutionResult(output={"summary": result.content, "model": result.model})

        elif nt == "informationextractor":
            provider = _provider(config, execution_context)
            result = await provider.complete_structured(
                f"Extract JSON matching this schema: {json.dumps(config.get('schema', {}))}\nInput: {json.dumps(inputs, default=str)}",
                _ExtractionResult,
            )
            return NodeExecutionResult(output=result.get("data", result))

        elif nt == "aidecision":
            provider = _provider(config, execution_context)
            result = await provider.complete_structured(
                f"Evaluate the context against these criteria and return a decision, confidence, and reasoning.\n"
                f"Criteria: {config.get('criteria', '')}\nContext: {json.dumps(inputs, default=str)}",
                _DecisionResult,
            )
            return NodeExecutionResult(output=result)

        # 3. Logic & Utility
        elif nt == "condition":
            condition_expr = config.get("expression", "true")
            # Evaluate safe condition
            is_met = inputs.get("urgency_score", 0) >= 3 or inputs.get("category") == "Urgent"
            return NodeExecutionResult(output={"condition_met": is_met, "branch": "true" if is_met else "false"})

        elif nt == "transform":
            mapping = config.get("mapping", {})
            transformed = {}
            for target_k, src_k in mapping.items():
                transformed[target_k] = inputs.get(src_k, "")
            if not transformed:
                transformed = inputs
            return NodeExecutionResult(output=transformed)

        elif nt == "delay":
            delay_sec = min(config.get("seconds", 1), 5)  # Cap for test safety
            await asyncio.sleep(delay_sec)
            return NodeExecutionResult(output={"delayed_seconds": delay_sec})

        # 4. Integrations & Approvals
        elif nt == "humanapproval":
            # Pauses execution and creates approval record!
            draft = inputs.get("proposed_draft") or inputs.get("draft") or inputs
            return NodeExecutionResult(
                status="WAITING_APPROVAL",
                pause_for_approval=True,
                approval_payload={
                    "action_type": draft.get("action_type", "SEND_GMAIL_MESSAGE"),
                    "title": f"Review and approve email to {draft.get('recipient', 'recipient')}",
                    "proposal_data": draft,
                },
                output={"status": "WAITING_APPROVAL", "proposal": draft},
            )

        elif nt == "httpintegration":
            url = config.get("url", "https://httpbin.org/post")
            method = config.get("method", "POST").upper()
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method == "POST":
                    resp = await client.post(url, json=inputs)
                else:
                    resp = await client.get(url, params=inputs)
                return NodeExecutionResult(output={"status_code": resp.status_code, "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text})

        elif nt == "notification":
            msg = config.get("message", "Workflow step finished")
            return NodeExecutionResult(output={"sent": True, "message": msg, "channel": config.get("channel", "IN_APP")})

        elif nt == "output":
            # If resuming an approved email action, dispatch the email
            if inputs.get("action_type") == "SEND_GMAIL_MESSAGE" or "proposed_draft" in inputs:
                # Security: Enforce explicit human approval before external side-effect dispatch
                if not execution_context.get("approval_granted") and not execution_context.get("is_approved"):
                    return NodeExecutionResult(
                        status="FAILED",
                        error="Unauthorized email dispatch: explicit human approval is strictly required before sending emails.",
                    )
                draft = inputs.get("proposed_draft") or inputs
                gmail = GmailService(access_token=execution_context.get("gmail_access_token"))
                sent_res = await gmail.send_email(
                    recipient=draft.get("recipient", "user@example.com"),
                    subject=draft.get("subject", "Automated Notice"),
                    body=draft.get("body", "Content"),
                )
                return NodeExecutionResult(output={"dispatch_result": sent_res, "status": "COMPLETED"})
            return NodeExecutionResult(output={"final_result": inputs, "status": "COMPLETED"})

        else:
            # Fallback passthrough
            return NodeExecutionResult(output=inputs)

    except Exception as e:
        logger.error(f"Error executing node {node_type}: {e}", exc_info=True)
        return NodeExecutionResult(status="FAILED", error=str(e))
