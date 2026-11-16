"""Analytics API: real database-backed metrics, performance, and trends."""

from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.database.models import (
    Workspace,
    Workflow,
    Execution,
    Approval,
    ExecutionStatus,
    AgentRun,
    Integration,
    AuditLog,
    AIUsageRecord,
)
from app.schemas.integration import AnalyticsOverviewResponse, TrendItem

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    # 1. Total & Active Workflows
    wf_res = await db.execute(
        select(
            func.count(Workflow.id),
            func.count(Workflow.id).filter(Workflow.is_active == True),
        ).where(Workflow.workspace_id == workspace.id)
    )
    total_wf, active_wf = wf_res.first() or (0, 0)

    # 2. Executions stats
    exc_res = await db.execute(
        select(
            func.count(Execution.id),
            func.count(Execution.id).filter(Execution.status == ExecutionStatus.COMPLETED.value),
            func.count(Execution.id).filter(Execution.status == ExecutionStatus.FAILED.value),
            func.avg(Execution.duration_ms).filter(Execution.duration_ms != None),
        ).where(Execution.workspace_id == workspace.id)
    )
    total_exc, succeeded, failed, avg_dur = exc_res.first() or (0, 0, 0, 0.0)
    total_exc = total_exc or 0
    succeeded = succeeded or 0
    failed = failed or 0
    success_rate = round((succeeded / total_exc * 100), 1) if total_exc > 0 else 0.0
    failure_rate = round((failed / total_exc * 100), 1) if total_exc > 0 else 0.0

    # 3. Pending approvals
    appr_res = await db.execute(
        select(func.count(Approval.id)).where(
            Approval.workspace_id == workspace.id, Approval.status == "PENDING"
        )
    )
    pending_approvals = appr_res.scalar() or 0

    # 4. Token Consumption & AI Usage (calculated strictly from persisted records)
    agent_tokens_res = await db.execute(
        select(func.sum(AgentRun.token_count)).where(AgentRun.workspace_id == workspace.id)
    )
    agent_tokens = agent_tokens_res.scalar() or 0

    usage_res = await db.execute(
        select(
            func.sum(AIUsageRecord.total_tokens),
            func.sum(AIUsageRecord.estimated_cost),
        ).where(AIUsageRecord.workspace_id == workspace.id)
    )
    recorded_tokens, recorded_cost = usage_res.first() or (0, 0.0)
    total_tokens = int(agent_tokens + (recorded_tokens or 0))
    estimated_cost = round(float(recorded_cost or (total_tokens * 0.000002)), 4)

    # 5. Connected Integrations
    int_res = await db.execute(
        select(Integration).where(
            Integration.workspace_id == workspace.id,
            Integration.is_connected == True,
        )
    )
    connected_integrations_list = [
        {
            "id": item.id,
            "provider": item.provider,
            "account_email": item.account_email,
            "connected_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in int_res.scalars().all()
    ]

    # 6. Recent executions
    recent_res = await db.execute(
        select(Execution, Workflow.name)
        .outerjoin(Workflow, Execution.workflow_id == Workflow.id)
        .where(Execution.workspace_id == workspace.id)
        .order_by(desc(Execution.started_at))
        .limit(6)
    )
    recent_activity = []
    for exc, wf_name in recent_res.all():
        recent_activity.append({
            "id": exc.id,
            "workflow_name": wf_name or "Autonomous Pipeline",
            "status": exc.status,
            "started_at": exc.started_at.isoformat() if exc.started_at else None,
            "duration_ms": exc.duration_ms or 0,
        })

    # 7. Recent Agent Activity
    agent_runs_res = await db.execute(
        select(AgentRun)
        .where(AgentRun.workspace_id == workspace.id)
        .order_by(desc(AgentRun.created_at))
        .limit(6)
    )
    recent_agent_runs = []
    for run in agent_runs_res.scalars().all():
        recent_agent_runs.append({
            "id": run.id,
            "task_id": run.task_id,
            "agent_role": run.agent_role,
            "status": run.status,
            "token_count": run.token_count,
            "latency_ms": run.latency_ms,
            "provider": run.provider,
            "model": run.model,
            "started_at": run.created_at.isoformat() if run.created_at else None,
        })

    # 8. Recent Audit Logs
    audit_res = await db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace.id)
        .order_by(desc(AuditLog.created_at))
        .limit(8)
    )
    recent_audit_logs = []
    for log in audit_res.scalars().all():
        recent_audit_logs.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    # 9. Real Trend Data (last 7 days)
    trends = []
    now = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        date_str = day_start.strftime("%b %d")

        # Query real counts for this specific 24h bucket
        day_counts = await db.execute(
            select(
                func.count(Execution.id),
                func.count(Execution.id).filter(Execution.status == ExecutionStatus.COMPLETED.value),
                func.count(Execution.id).filter(Execution.status == ExecutionStatus.FAILED.value),
            ).where(
                Execution.workspace_id == workspace.id,
                Execution.started_at >= day_start,
                Execution.started_at < day_end,
            )
        )
        total_d, succ_d, fail_d = day_counts.first() or (0, 0, 0)
        trends.append(
            TrendItem(
                date=date_str,
                executions=total_d or 0,
                successes=succ_d or 0,
                failures=fail_d or 0,
            )
        )

    return AnalyticsOverviewResponse(
        total_workflows=total_wf or 0,
        active_workflows=active_wf or 0,
        total_executions=total_exc,
        successful_executions=succeeded,
        failed_executions=failed,
        success_rate_percent=success_rate,
        failure_rate_percent=failure_rate,
        pending_approvals=pending_approvals,
        avg_duration_ms=round(float(avg_dur or 0.0), 1),
        total_tokens_consumed=total_tokens,
        estimated_cost_usd=estimated_cost,
        connected_integrations_count=len(connected_integrations_list),
        connected_integrations=connected_integrations_list,
        recent_agent_runs=recent_agent_runs,
        recent_audit_logs=recent_audit_logs,
        execution_trends=trends,
        recent_activity=recent_activity,
    )
