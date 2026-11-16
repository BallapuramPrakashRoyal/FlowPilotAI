"""FastAPI Authentication and RBAC dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.database.models import User, Workspace, WorkspaceMember, RoleEnum

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer token and retrieve active user."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


async def get_current_workspace(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Retrieve active workspace and verify membership."""
    if x_workspace_id:
        result = await db.execute(
            select(Workspace, WorkspaceMember)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(
                Workspace.id == x_workspace_id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        row = result.first()
        if not row:
            # Check if user owns it
            own_res = await db.execute(
                select(Workspace).where(Workspace.id == x_workspace_id, Workspace.owner_id == current_user.id)
            )
            own_ws = own_res.scalars().first()
            if not own_ws:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to requested workspace",
                )
            return own_ws
        return row[0]

    # Default to first workspace owned or joined
    result = await db.execute(
        select(Workspace)
        .outerjoin(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where((Workspace.owner_id == current_user.id) | (WorkspaceMember.user_id == current_user.id))
        .limit(1)
    )
    workspace = result.scalars().first()

    if not workspace:
        # Auto-create personal workspace if none exists
        workspace = Workspace(
            name=f"{current_user.full_name}'s Workspace",
            slug=f"ws-{current_user.id[:8]}",
            owner_id=current_user.id,
        )
        db.add(workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=RoleEnum.OWNER.value,
        )
        db.add(member)
        await db.commit()
        await db.refresh(workspace)

    return workspace
