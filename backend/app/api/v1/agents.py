"""Workspace-scoped multi-agent planning, execution, and observability APIs."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.contracts import AgentTask, PlanResult
from app.ai.agents.orchestrator import MultiAgentOrchestrator, OrchestrationLimits
from app.ai.agents.tools import TOOL_REGISTRY
from app.core.dependencies import get_current_workspace
from app.core.database import get_db
from app.database.models import Workspace, AgentRun, Execution, ExecutionStatus, Workflow
from app.workers.tasks import execute_agent_plan_task

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentPlanRequest(BaseModel):
    objective: str = Field(min_length=5, max_length=10000)


class AgentRunRequest(BaseModel):
    plan: PlanResult
    input: Dict[str, Any] = Field(default_factory=dict)
    permissions: set[str] = Field(default_factory=set)
    max_iterations: int = Field(default=8, ge=1, le=50)
    async_dispatch: bool = False
    execution_id: Optional[str] = None


class AgentRunResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    agent_role: str
    status: str
    token_count: int
    latency_ms: int
    retry_count: int
    provider: Optional[str] = None
    model: Optional[str] = None
    tools_called: List[Dict[str, Any]] = Field(default_factory=list)
    task_input: Dict[str, Any] = Field(default_factory=dict)
    task_output: Dict[str, Any] = Field(default_factory=dict)
    handoff_data: Dict[str, Any] = Field(default_factory=dict)
    validation_findings: List[str] = Field(default_factory=list)
    approval_status: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


@router.get("/tools")
async def list_agent_tools(workspace: Workspace = Depends(get_current_workspace)):
    """List all registered, server-owned agent tools and their required permissions."""
    del workspace
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "required_permissions": sorted(tool.required_permissions),
            "requires_approval": tool.requires_approval,
            "timeout_seconds": tool.timeout_seconds,
        }
        for tool in TOOL_REGISTRY.values()
    ]


@router.post("/plan", response_model=PlanResult)
async def plan_agent_tasks(
    payload: AgentPlanRequest,
    workspace: Workspace = Depends(get_current_workspace),
):
    del workspace
    text = payload.objective.lower()
    tasks = [
        AgentTask(task_id="analyze", agent="Analyst", objective=payload.objective),
        AgentTask(task_id="validate", agent="Validator", objective="Validate findings and recommendations", depends_on=["analyze"]),
    ]
    tools = []
    if "knowledge" in text or "research" in text or "retrieve" in text or "search" in text:
        tasks.insert(0, AgentTask(task_id="research", agent="Researcher", objective=payload.objective))
        tasks[1].depends_on = ["research"]
        tools.append("knowledge.retrieve")

    if "gmail" in text or "email" in text or "send" in text or "draft" in text:
        tasks.append(
            AgentTask(
                task_id="execute_draft",
                agent="Executor",
                objective="Create email draft from analyzed findings",
                depends_on=["validate"],
                sensitive=False,
            )
        )
        tools.append("gmail.create_draft")

    return PlanResult(tasks=tasks, tools=tools)


@router.post("/run")
async def run_agent_plan(
    payload: AgentRunRequest,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    # Verify tools exist in registry
    if any(tool not in TOOL_REGISTRY for tool in payload.plan.tools):
        raise HTTPException(status_code=422, detail="Plan contains an unregistered tool")

    # If execution_id is not provided, create a persistent Execution record
    execution_id = payload.execution_id
    if not execution_id:
        wf_res = await db.execute(
            select(Workflow).where(Workflow.workspace_id == workspace.id).limit(1)
        )
        wf = wf_res.scalars().first()
        if not wf:
            wf = Workflow(
                workspace_id=workspace.id,
                name="Agent Orchestration Workflow",
                description="System workflow for dynamic multi-agent execution plans",
                is_active=True,
            )
            db.add(wf)
            await db.flush()

        execution = Execution(
            workspace_id=workspace.id,
            workflow_id=wf.id,
            workflow_version_id=wf.current_version_id or "v1",
            status=ExecutionStatus.QUEUED.value if payload.async_dispatch else ExecutionStatus.RUNNING.value,
            trigger_type="AGENT_PLAN",
            context_data={
                "agent_plan": payload.plan.model_dump(),
                "initial_input": payload.input,
                "permissions": list(payload.permissions),
            },
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        execution_id = execution.id

    # If async execution requested, dispatch to Celery background worker with local fallback
    if payload.async_dispatch:
        dispatched_celery = False
        from app.workers.celery_app import is_redis_available
        if is_redis_available():
            try:
                execute_agent_plan_task.apply_async(
                    kwargs={
                        "execution_id": execution_id,
                        "plan_dict": payload.plan.model_dump(),
                        "workspace_id": workspace.id,
                        "permissions": list(payload.permissions),
                        "initial_input": payload.input,
                        "limits_dict": {"max_iterations": payload.max_iterations},
                    },
                    connect_timeout=1,
                    retry=False,
                )
                dispatched_celery = True
            except Exception:
                pass

        if not dispatched_celery:
            async def _bg_run():
                orchestrator = MultiAgentOrchestrator(
                    OrchestrationLimits(max_iterations=payload.max_iterations)
                )
                from app.core import database
                from app.database.models import Execution, ExecutionStatus
                from datetime import datetime, timezone
                async with database.AsyncSessionLocal() as session:
                    exec_res = await session.execute(select(Execution).where(Execution.id == execution_id))
                    exc = exec_res.scalars().first()
                    if exc and exc.status == ExecutionStatus.QUEUED.value:
                        exc.status = ExecutionStatus.RUNNING.value
                        exc.started_at = datetime.now(timezone.utc)
                        await session.commit()

                    result = await orchestrator.run(
                        plan=payload.plan,
                        workspace_id=workspace.id,
                        permissions=payload.permissions,
                        initial_input=payload.input,
                        db=session,
                        execution_id=execution_id,
                    )

                    exec_res2 = await session.execute(select(Execution).where(Execution.id == execution_id))
                    exc2 = exec_res2.scalars().first()
                    if exc2:
                        if result.status == "COMPLETED":
                            exc2.status = ExecutionStatus.COMPLETED.value
                            exc2.completed_at = datetime.now(timezone.utc)
                            if exc2.started_at:
                                diff = exc2.completed_at - exc2.started_at
                                exc2.duration_ms = int(diff.total_seconds() * 1000)
                        elif result.status == "WAITING_APPROVAL":
                            exc2.status = ExecutionStatus.WAITING_APPROVAL.value
                        elif result.status == "CANCELLED":
                            exc2.status = ExecutionStatus.CANCELLED.value
                            exc2.completed_at = datetime.now(timezone.utc)
                        else:
                            exc2.status = ExecutionStatus.FAILED.value
                            exc2.completed_at = datetime.now(timezone.utc)
                        await session.commit()
            background_tasks.add_task(_bg_run)

        return {
            "execution_id": execution_id,
            "status": "QUEUED",
            "message": "Agent plan dispatched asynchronously to Celery worker" if dispatched_celery else "Agent plan dispatched to background runner",
        }

    # Otherwise execute synchronously with durable state persistence
    orchestrator = MultiAgentOrchestrator(
        OrchestrationLimits(max_iterations=payload.max_iterations)
    )
    result = await orchestrator.run(
        plan=payload.plan,
        workspace_id=workspace.id,
        permissions=payload.permissions,
        initial_input=payload.input,
        db=db,
        execution_id=execution_id,
    )

    # Update execution record
    exec_res = await db.execute(select(Execution).where(Execution.id == execution_id))
    exc = exec_res.scalars().first()
    if exc:
        exc.status = result.status
        if result.status == "COMPLETED":
            exc.completed_at = datetime.now(timezone.utc)
        await db.commit()

    res_dict = result.model_dump()
    res_dict["execution_id"] = execution_id
    return res_dict


@router.post("/runs/{execution_id}/cancel")
async def cancel_agent_run(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an active or queued agent plan execution."""
    res = await db.execute(
        select(Execution).where(Execution.id == execution_id, Execution.workspace_id == workspace.id)
    )
    exc = res.scalars().first()
    if not exc:
        raise HTTPException(status_code=404, detail="Execution not found")

    exc.status = ExecutionStatus.CANCELLED.value
    exc.completed_at = datetime.now(timezone.utc)

    # Mark non-completed agent runs as CANCELLED
    await db.execute(
        update(AgentRun)
        .where(
            AgentRun.execution_id == execution_id,
            AgentRun.workspace_id == workspace.id,
            AgentRun.status.in_(["RUNNING", "QUEUED", "WAITING_APPROVAL"]),
        )
        .values(status="CANCELLED")
    )
    await db.commit()
    return {"status": "CANCELLED", "execution_id": execution_id}


@router.post("/runs/{execution_id}/resume")
async def resume_agent_run(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Resume an interrupted or approval-paused agent plan, skipping completed tasks."""
    res = await db.execute(
        select(Execution).where(Execution.id == execution_id, Execution.workspace_id == workspace.id)
    )
    exc = res.scalars().first()
    if not exc:
        raise HTTPException(status_code=404, detail="Execution not found")

    plan_data = (exc.context_data or {}).get("agent_plan")
    if not plan_data:
        raise HTTPException(status_code=400, detail="Execution does not contain an agent plan to resume")

    plan = PlanResult.model_validate(plan_data)
    permissions = set((exc.context_data or {}).get("permissions", []))
    initial_input = (exc.context_data or {}).get("initial_input", {})

    exc.status = ExecutionStatus.RUNNING.value
    await db.commit()

    orchestrator = MultiAgentOrchestrator()
    result = await orchestrator.run(
        plan=plan,
        workspace_id=workspace.id,
        permissions=permissions,
        initial_input=initial_input,
        db=db,
        execution_id=execution_id,
        is_approved=True,
    )

    exc.status = result.status
    if result.status == "COMPLETED":
        exc.completed_at = datetime.now(timezone.utc)
    await db.commit()

    res_dict = result.model_dump()
    res_dict["execution_id"] = execution_id
    return res_dict


@router.get("/runs/{execution_id}", response_model=List[AgentRunResponse])
async def list_agent_runs(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full agent observability records for an execution."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.execution_id == execution_id, AgentRun.workspace_id == workspace.id)
        .order_by(AgentRun.created_at)
    )
    runs = result.scalars().all()
    return [
        AgentRunResponse(
            id=run.id,
            task_id=run.task_id,
            agent_role=run.agent_role,
            status=run.status,
            token_count=run.token_count,
            latency_ms=run.latency_ms,
            retry_count=run.retry_count,
            provider=run.provider,
            model=run.model,
            tools_called=run.tools_called or [],
            task_input=run.task_input or {},
            task_output=run.task_output or {},
            handoff_data=run.handoff_data or {},
            validation_findings=run.validation_findings or [],
            approval_status=run.approval_status,
            error_message=run.error_message,
            created_at=run.created_at,
        )
        for run in runs
    ]
