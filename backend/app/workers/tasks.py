"""Celery background worker tasks for asynchronous execution."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.engine.runner import WorkflowExecutionRunner
from app.core import database
from app.database.models import Execution, ExecutionStatus, AgentRun

logger = logging.getLogger(__name__)


@celery_app.task(name="execute_workflow_task", bind=True, max_retries=3)
def execute_workflow_task(self, execution_id: str, initial_context: dict = None):
    """Execute workflow asynchronously inside Celery worker."""
    logger.info(f"Celery executing workflow task: {execution_id}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        status = loop.run_until_complete(
            WorkflowExecutionRunner.start_execution(execution_id, initial_context)
        )
        return {"execution_id": execution_id, "status": status.value}
    except Exception as exc:
        logger.error(f"Celery task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=5)
    finally:
        loop.close()


@celery_app.task(name="execute_agent_plan_task", bind=True, max_retries=3)
def execute_agent_plan_task(
    self,
    execution_id: str,
    plan_dict: dict,
    workspace_id: str,
    permissions: list,
    initial_input: dict,
    limits_dict: dict = None,
    is_approved: bool = False,
):
    """Execute multi-agent plan asynchronously inside Celery worker with full state persistence."""
    logger.info(f"Celery executing agent plan for execution {execution_id}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.ai.agents.contracts import PlanResult
        from app.ai.agents.orchestrator import MultiAgentOrchestrator, OrchestrationLimits

        plan = PlanResult.model_validate(plan_dict)
        limits = OrchestrationLimits.model_validate(limits_dict) if limits_dict else OrchestrationLimits()

        async def _run():
            async with database.AsyncSessionLocal() as session:
                exec_res = await session.execute(select(Execution).where(Execution.id == execution_id))
                exc = exec_res.scalars().first()
                if exc and exc.status == ExecutionStatus.QUEUED.value:
                    exc.status = ExecutionStatus.RUNNING.value
                    exc.started_at = datetime.now(timezone.utc)
                    await session.commit()

                orchestrator = MultiAgentOrchestrator(limits=limits)
                result = await orchestrator.run(
                    plan=plan,
                    workspace_id=workspace_id,
                    permissions=set(permissions),
                    initial_input=initial_input,
                    db=session,
                    execution_id=execution_id,
                    is_approved=is_approved,
                )

                # Persist execution status
                if exc:
                    if result.status == "COMPLETED":
                        exc.status = ExecutionStatus.COMPLETED.value
                        exc.completed_at = datetime.now(timezone.utc)
                        if exc.started_at:
                            diff = exc.completed_at - exc.started_at
                            exc.duration_ms = int(diff.total_seconds() * 1000)
                    elif result.status == "WAITING_APPROVAL":
                        exc.status = ExecutionStatus.WAITING_APPROVAL.value
                    elif result.status == "CANCELLED":
                        exc.status = ExecutionStatus.CANCELLED.value
                        exc.completed_at = datetime.now(timezone.utc)
                    else:
                        exc.status = ExecutionStatus.FAILED.value
                        exc.completed_at = datetime.now(timezone.utc)
                        exc.error_message = "; ".join(result.findings) or "Agent execution failed"
                    await session.commit()

                return result.model_dump()

        return loop.run_until_complete(_run())
    except Exception as exc:
        logger.error(f"Agent plan Celery task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=5)
    finally:
        loop.close()


@celery_app.task(name="recover_interrupted_executions")
def recover_interrupted_executions():
    """Requeue workflow and agent plan executions left running or queued after a worker crash."""
    async def recover():
        async with database.AsyncSessionLocal() as session:
            result = await session.execute(
                select(Execution).where(
                    Execution.status.in_([ExecutionStatus.RUNNING.value, ExecutionStatus.QUEUED.value]),
                    Execution.started_at < datetime.now(timezone.utc) - timedelta(minutes=10),
                )
            )
            executions = result.scalars().all()
            for execution in executions:
                execution.status = ExecutionStatus.QUEUED.value
                plan_data = (execution.context_data or {}).get("agent_plan")
                if plan_data:
                    execute_agent_plan_task.delay(
                        execution.id,
                        plan_data,
                        execution.workspace_id,
                        (execution.context_data or {}).get("permissions", []),
                        (execution.context_data or {}).get("initial_input", {}),
                    )
                else:
                    execute_workflow_task.delay(execution.id, {})
            await session.commit()
            return len(executions)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(recover())
    finally:
        loop.close()
