"""Provider discovery and health APIs for the AI runtime."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.ai.providers.factory import get_ai_provider
from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_workspace
from app.core.security import encrypt_secret
from app.database.models import Workspace, WorkspaceAIConfig, AIUsageRecord
from app.schemas.ai import AIConfigResponse, AIConfigUpdate

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/providers")
async def list_ai_providers(workspace: Workspace = Depends(get_current_workspace)) -> List[Dict[str, Any]]:
    del workspace
    providers = [
        {"id": "gemini", "configured": bool(settings.GEMINI_API_KEY), "models": ["gemini-1.5-pro"]},
        {"id": "ollama", "configured": True, "models": ["llama3:latest"]},
        {"id": "openai-compatible", "configured": bool(settings.OPENAI_API_KEY), "models": [settings.OPENAI_MODEL]},
        {"id": "mock", "configured": True, "models": ["flowpilot-mock-deterministic-v1"]},
    ]
    return providers


@router.get("/providers/{provider_name}/health")
async def ai_provider_health(
    provider_name: str,
    workspace: Workspace = Depends(get_current_workspace),
) -> Dict[str, Any]:
    del workspace
    provider = get_ai_provider(provider_name)
    configured = {
        "mock": True,
        "gemini": bool(settings.GEMINI_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "openai-compatible": bool(settings.OPENAI_API_KEY),
    }.get(provider_name, True)
    return {"provider": provider_name, "healthy": configured and await provider.health_check()}


@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkspaceAIConfig).where(WorkspaceAIConfig.workspace_id == workspace.id))
    config = result.scalars().first()
    if not config:
        config = WorkspaceAIConfig(workspace_id=workspace.id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return AIConfigResponse.model_validate(config, from_attributes=True)


@router.put("/config", response_model=AIConfigResponse)
async def update_ai_config(
    payload: AIConfigUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    provider = get_ai_provider(payload.default_provider)
    configured = {
        "mock": True,
        "gemini": bool(settings.GEMINI_API_KEY),
        "openai": bool(settings.OPENAI_API_KEY),
        "openai-compatible": bool(settings.OPENAI_API_KEY),
    }.get(payload.default_provider, True)
    if payload.default_provider != "mock" and (not configured or not await provider.health_check()):
        raise HTTPException(status_code=422, detail="Selected AI provider is not configured or available")
    result = await db.execute(select(WorkspaceAIConfig).where(WorkspaceAIConfig.workspace_id == workspace.id))
    config = result.scalars().first()
    if not config:
        config = WorkspaceAIConfig(workspace_id=workspace.id)
        db.add(config)
    config.default_provider = payload.default_provider
    config.default_model = payload.default_model
    config.request_limit = payload.request_limit
    config.daily_token_limit = payload.daily_token_limit
    config.pricing_json = payload.pricing
    config.sensitive_fields = payload.sensitive_fields
    if payload.api_key:
        config.encrypted_api_key = encrypt_secret(payload.api_key)
    await db.commit()
    await db.refresh(config)
    return AIConfigResponse.model_validate(config, from_attributes=True)


@router.get("/usage")
async def get_ai_usage(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIUsageRecord).where(AIUsageRecord.workspace_id == workspace.id).order_by(AIUsageRecord.created_at.desc()).limit(500)
    )
    records = result.scalars().all()
    return [
        {
            "provider": record.provider,
            "model": record.model,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "total_tokens": record.total_tokens,
            "estimated_cost": record.estimated_cost,
            "created_at": record.created_at,
        }
        for record in records
    ]
