import pytest
from pydantic import BaseModel

from app.ai.providers.factory import get_ai_provider
from app.ai.providers.mock import MockAIProvider
from app.engine.handlers import execute_node
from app.core.redaction import redact


@pytest.mark.asyncio
async def test_mock_provider_structured_output_is_schema_valid():
    provider = MockAIProvider()
    result = await provider.complete_structured("classify this", _Result)
    assert _Result.model_validate(result).value


@pytest.mark.asyncio
async def test_llm_node_resolves_nested_workflow_variables():
    result = await execute_node(
        "llmCompletion",
        {"prompt": "Summarize {{email.body}}"},
        {"email": {"body": "Important message"}},
        {},
    )
    assert result.status == "SUCCEEDED"
    assert result.output["provider"] == "mock"


@pytest.mark.asyncio
async def test_missing_workflow_variable_fails_explicitly():
    result = await execute_node(
        "llmCompletion",
        {"prompt": "Use {{missing.value}}"},
        {},
        {},
    )
    assert result.status == "FAILED"
    assert "Missing workflow variable" in (result.error or "")


def test_redaction_removes_credentials_from_nested_trace():
    payload = {
        "authorization": "Bearer secret-token",
        "nested": {"api_key": "secret", "message": "safe"},
    }
    result = redact(payload)
    assert result["authorization"] == "[REDACTED]"
    assert result["nested"]["api_key"] == "[REDACTED]"
    assert result["nested"]["message"] == "safe"


class _Result(BaseModel):
    value: str = "ok"
