import pytest

from app.ai.agents.contracts import AgentTask, PlanResult
from app.ai.agents.orchestrator import MultiAgentOrchestrator, OrchestrationLimits
from app.ai.agents.tools import ToolContext, invoke_tool


@pytest.mark.asyncio
async def test_tool_registry_rejects_missing_permission():
    with pytest.raises(PermissionError):
        await invoke_tool("knowledge.retrieve", {"query": "secret"}, ToolContext(workspace_id="w"))


@pytest.mark.asyncio
async def test_orchestrator_handoffs_dependencies_deterministically():
    plan = PlanResult(tasks=[
        AgentTask(task_id="first", agent="Analyst", objective="analyze"),
        AgentTask(task_id="second", agent="Validator", objective="validate", depends_on=["first"]),
    ])
    result = await MultiAgentOrchestrator().run(plan, "w", set(), {"text": "hello"})
    assert result.status == "COMPLETED"
    assert [handoff.task_id for handoff in result.handoffs] == ["first", "second"]


@pytest.mark.asyncio
async def test_orchestrator_enforces_iteration_limit_and_approval():
    plan = PlanResult(tasks=[
        AgentTask(task_id="sensitive", agent="Executor", objective="send", sensitive=True),
    ])
    result = await MultiAgentOrchestrator(OrchestrationLimits(max_iterations=1)).run(plan, "w", set(), {})
    assert result.status == "WAITING_APPROVAL"
