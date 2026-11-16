"""Executions API: inspect, cancel, and stream execution traces."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.database.models import Workspace, Execution, ExecutionNode, ExecutionEvent, ExecutionStatus
from app.schemas.execution import ExecutionResponse, ExecutionNodeResponse, ExecutionEventResponse
from app.core.redaction import redact

router = APIRouter(prefix="/executions", tags=["Executions"])


def _safe_node(node: ExecutionNode) -> ExecutionNodeResponse:
    return ExecutionNodeResponse(
        id=node.id,
        node_id=node.node_id,
        node_type=node.node_type,
        status=node.status,
        inputs=redact(node.inputs or {}),
        outputs=redact(node.outputs or {}),
        error_message=node.error_message,
        started_at=node.started_at,
        completed_at=node.completed_at,
        retry_count=node.retry_count,
    )


@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Execution).where(Execution.workspace_id == workspace.id).order_by(desc(Execution.started_at))
    )
    executions = res.scalars().all()
    results = []
    for exc in executions:
        # Load nodes
        n_res = await db.execute(select(ExecutionNode).where(ExecutionNode.execution_id == exc.id))
        nodes = n_res.scalars().all()
        results.append(
            ExecutionResponse(
                id=exc.id,
                workspace_id=exc.workspace_id,
                workflow_id=exc.workflow_id,
                workflow_version_id=exc.workflow_version_id,
                status=exc.status,
                trigger_type=exc.trigger_type,
                context_data=redact(exc.context_data or {}),
                error_message=exc.error_message,
                started_at=exc.started_at,
                completed_at=exc.completed_at,
                duration_ms=exc.duration_ms,
                token_usage=exc.token_usage or {},
                nodes=[_safe_node(n) for n in nodes],
                events=[ExecutionEventResponse.model_validate(e) for e in exc.events],
            )
        )
    return results


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Execution).where(Execution.id == execution_id, Execution.workspace_id == workspace.id)
    )
    exc = res.scalars().first()
    if not exc:
        raise HTTPException(status_code=404, detail="Execution not found")

    n_res = await db.execute(select(ExecutionNode).where(ExecutionNode.execution_id == exc.id))
    nodes = n_res.scalars().all()

    return ExecutionResponse(
        id=exc.id,
        workspace_id=exc.workspace_id,
        workflow_id=exc.workflow_id,
        workflow_version_id=exc.workflow_version_id,
        status=exc.status,
        trigger_type=exc.trigger_type,
        context_data=redact(exc.context_data or {}),
        error_message=exc.error_message,
        started_at=exc.started_at,
        completed_at=exc.completed_at,
        duration_ms=exc.duration_ms,
        token_usage=exc.token_usage or {},
        nodes=[_safe_node(n) for n in nodes],
        events=[ExecutionEventResponse.model_validate(e) for e in exc.events],
    )


@router.get("/{execution_id}/events", response_model=List[ExecutionEventResponse])
async def get_execution_events(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ExecutionEvent)
        .join(Execution, Execution.id == ExecutionEvent.execution_id)
        .where(ExecutionEvent.execution_id == execution_id, Execution.workspace_id == workspace.id)
        .order_by(ExecutionEvent.created_at)
    )
    events = res.scalars().all()
    return [
        ExecutionEventResponse(
            id=event.id,
            event_type=event.event_type,
            payload=redact(event.payload),
            created_at=event.created_at,
        )
        for event in events
    ]


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Execution).where(Execution.id == execution_id, Execution.workspace_id == workspace.id)
    )
    exc = res.scalars().first()
    if not exc:
        raise HTTPException(status_code=404, detail="Execution not found")

    exc.status = ExecutionStatus.CANCELLED.value
    await db.commit()
    return {"status": "CANCELLED", "execution_id": execution_id}
