"""Human-in-the-loop Approval Center API endpoints."""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.database.models import User, Workspace, Approval, ApprovalStatus
from app.schemas.execution import ApprovalDecisionRequest, ApprovalResponse
from app.engine.runner import WorkflowExecutionRunner

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/", response_model=List[ApprovalResponse])
async def list_pending_approvals(
    status_filter: str = "PENDING",
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    query = select(Approval).where(Approval.workspace_id == workspace.id)
    if status_filter:
        query = query.where(Approval.status == status_filter)
    query = query.order_by(desc(Approval.created_at))

    res = await db.execute(query)
    approvals = res.scalars().all()
    return [ApprovalResponse.model_validate(a) for a in approvals]


@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a paused workflow execution and trigger resumption."""
    res = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.workspace_id == workspace.id)
    )
    approval = res.scalars().first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Approval has already been resolved as {approval.status}")

    decision = payload.decision.upper()
    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be 'APPROVED' or 'REJECTED'")

    approval.status = decision
    approval.decision_notes = payload.decision_notes
    approval.decided_by = current_user.id
    approval.decided_at = datetime.now(timezone.utc)
    if payload.edited_proposal:
        approval.proposal_data = payload.edited_proposal

    await db.commit()
    await db.refresh(approval)

    from app.core.audit import log_audit_event
    await log_audit_event(
        db=db,
        workspace_id=workspace.id,
        action=f"APPROVAL_{decision}",
        resource_type="approval",
        resource_id=approval.id,
        user_id=current_user.id,
        details={"decision": decision, "notes": payload.decision_notes},
    )

    # Resume the workflow execution runner asynchronously
    background_tasks.add_task(
        WorkflowExecutionRunner.resume_after_approval,
        approval_id=approval.id,
        decision=decision,
        decision_notes=payload.decision_notes,
        edited_proposal=payload.edited_proposal,
        decided_by=current_user.id,
    )

    return ApprovalResponse.model_validate(approval)
