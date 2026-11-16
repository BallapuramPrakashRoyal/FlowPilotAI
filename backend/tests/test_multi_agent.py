"""Unit tests for Multi-Agent AI runtime and supervisor."""

import pytest
from app.ai.agents.runtime import MultiAgentSupervisor, AnalystAgent, ExecutorAgent, ValidatorAgent
from app.ai.providers.mock import MockAIProvider


@pytest.mark.asyncio
async def test_analyst_agent():
    provider = MockAIProvider()
    analyst = AnalystAgent(provider)
    result = await analyst.analyze_text(
        "CRITICAL: Immediate incident on checkout service! Need resolution ASAP.",
        categories=["Urgent", "Important", "Spam"],
    )
    assert result["urgency_score"] >= 4
    assert "Urgent" in result["category"]


@pytest.mark.asyncio
async def test_executor_agent():
    provider = MockAIProvider()
    executor = ExecutorAgent(provider)
    draft = await executor.prepare_email_draft(
        recipient="vp@example.com",
        subject="Incident Response",
        context="Issue acknowledged, investigating root cause.",
    )
    assert draft["recipient"] == "vp@example.com"
    assert "Incident Response" in draft["subject"]
    assert draft["action_type"] == "SEND_GMAIL_MESSAGE"


@pytest.mark.asyncio
async def test_supervisor_pipeline():
    supervisor = MultiAgentSupervisor(provider_name="mock")
    res = await supervisor.run_triaging_pipeline(
        email_sender="client@enterprise.com",
        email_subject="Urgent Security Escalation",
        email_body="Our production keys were compromised. Please revoke immediately.",
    )
    assert res.status == "COMPLETED"
    assert res.output["analysis"]["urgency_score"] >= 4
    assert res.output["proposed_draft"]["recipient"] == "client@enterprise.com"
    assert res.output["validation"]["is_valid"] is True
