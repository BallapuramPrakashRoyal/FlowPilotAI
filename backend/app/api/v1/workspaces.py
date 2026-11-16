"""Workspaces and Membership API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.models import User, Workspace, WorkspaceMember, RoleEnum
from app.schemas.auth import WorkspaceCreate, WorkspaceResponse, WorkspaceMemberResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workspaces owned by or shared with current user."""
    res = await db.execute(
        select(Workspace)
        .outerjoin(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where((Workspace.owner_id == current_user.id) | (WorkspaceMember.user_id == current_user.id))
        .distinct()
    )
    workspaces = res.scalars().all()
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    slug = payload.slug or (payload.name.lower().replace(" ", "-") + f"-{current_user.id[:6]}")
    ws = Workspace(name=payload.name, slug=slug, owner_id=current_user.id)
    db.add(ws)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=current_user.id,
        role=RoleEnum.OWNER.value,
    )
    db.add(member)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = []
    for member, user in res.all():
        m_dict = {
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": member.created_at,
        }
        members.append(WorkspaceMemberResponse(**m_dict))
    return members
