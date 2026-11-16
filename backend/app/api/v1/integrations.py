"""Integrations API: Google OAuth 2.0, token refresh, authorized Gmail operations, and marketplace status."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_workspace
from app.core.security import encrypt_secret, decrypt_secret, create_access_token, decode_access_token
from app.database.models import Workspace, Integration, IntegrationCredential, AuditLog
from app.schemas.integration import IntegrationResponse, IntegrationConnectRequest, GmailActionPreview
from app.integrations.gmail.service import GmailService, GMAIL_SCOPES

router = APIRouter(prefix="/integrations", tags=["Integrations"])


async def _get_valid_access_token(
    credential: IntegrationCredential,
    db: AsyncSession,
) -> str:
    """Retrieve decrypted access token, automatically refreshing if expired or expiring soon."""
    now = datetime.now(timezone.utc)
    if credential.token_expiry and credential.token_expiry < (now + timedelta(minutes=2)):
        if credential.encrypted_refresh_token:
            refresh_token = decrypt_secret(credential.encrypted_refresh_token)
            try:
                refreshed = await GmailService.refresh_access_token(refresh_token)
                new_token = refreshed.get("access_token")
                if new_token:
                    credential.encrypted_token = encrypt_secret(new_token)
                    expires_in = int(refreshed.get("expires_in", 3600))
                    credential.token_expiry = now + timedelta(seconds=expires_in)
                    await db.commit()
                    return new_token
            except Exception as exc:
                raise HTTPException(
                    status_code=401,
                    detail=f"Gmail token refresh failed: {exc}. Please reconnect your Gmail account.",
                ) from exc

    return decrypt_secret(credential.encrypted_token)


@router.get("/config")
async def get_integration_config():
    """Return workspace integration configuration status and OAuth readiness."""
    configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {
        "google_oauth_configured": configured,
        "google_client_id_configured": bool(settings.GOOGLE_CLIENT_ID),
        "google_redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scopes": GMAIL_SCOPES,
        "setup_instructions": (
            "Configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable live Gmail OAuth 2.0 integration."
            if not configured
            else "Google OAuth 2.0 is configured and ready for workspace authorization."
        ),
    }


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List integration statuses in the workspace."""
    res = await db.execute(select(Integration).where(Integration.workspace_id == workspace.id))
    existing = {i.provider: i for i in res.scalars().all()}

    providers = ["GMAIL", "GITHUB", "SLACK"]
    for p in providers:
        if p not in existing:
            new_int = Integration(
                workspace_id=workspace.id,
                provider=p,
                is_connected=False,
                status_message="Not connected" if p == "GMAIL" else "Coming soon",
            )
            db.add(new_int)
            existing[p] = new_int

    await db.commit()
    responses = []
    for p in providers:
        await db.refresh(existing[p])
        cred_res = await db.execute(
            select(IntegrationCredential).where(IntegrationCredential.integration_id == existing[p].id)
        )
        cred = cred_res.scalars().first()
        scopes = cred.scopes if cred and cred.scopes else ([] if p != "GMAIL" else GMAIL_SCOPES if existing[p].is_connected else [])
        resp_obj = IntegrationResponse(
            id=existing[p].id,
            workspace_id=existing[p].workspace_id,
            provider=existing[p].provider,
            is_connected=existing[p].is_connected,
            account_email=existing[p].account_email,
            status_message=existing[p].status_message,
            scopes=scopes,
            created_at=existing[p].created_at,
            updated_at=existing[p].updated_at,
        )
        responses.append(resp_obj)

    return responses


@router.post("/connect", response_model=IntegrationResponse)
async def connect_integration(
    payload: IntegrationConnectRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    provider = payload.provider.upper()
    if provider != "GMAIL":
        raise HTTPException(status_code=400, detail=f"Integration '{provider}' is currently planned")
    if payload.mock_mode:
        raise HTTPException(status_code=400, detail="Mock Gmail connections are not supported. Live OAuth 2.0 authorization is required.")
    if not payload.auth_code:
        raise HTTPException(status_code=400, detail="OAuth authorization code is required")

    res = await db.execute(
        select(Integration).where(Integration.workspace_id == workspace.id, Integration.provider == "GMAIL")
    )
    integration = res.scalars().first()
    if not integration:
        integration = Integration(workspace_id=workspace.id, provider="GMAIL")
        db.add(integration)
        await db.flush()

    try:
        token_response = await GmailService.exchange_code(payload.auth_code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google OAuth token exchange failed: {exc}") from exc

    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Google OAuth token exchange failed: no access token returned")

    integration.is_connected = True
    integration.account_email = token_response.get("email")
    integration.status_message = "Connected (OAuth Active)"

    # Store encrypted credentials
    cred_res = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id)
    )
    cred = cred_res.scalars().first()
    expires_in = int(token_response.get("expires_in", 3600))
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if not cred:
        cred = IntegrationCredential(
            integration_id=integration.id,
            encrypted_token=encrypt_secret(access_token),
            encrypted_refresh_token=encrypt_secret(token_response["refresh_token"]) if token_response.get("refresh_token") else None,
            token_expiry=expiry,
            scopes=token_response.get("scope", "").split() or GMAIL_SCOPES,
        )
        db.add(cred)
    else:
        cred.encrypted_token = encrypt_secret(access_token)
        cred.token_expiry = expiry
        if token_response.get("refresh_token"):
            cred.encrypted_refresh_token = encrypt_secret(token_response["refresh_token"])
        cred.scopes = token_response.get("scope", "").split() or GMAIL_SCOPES

    # Record Audit Log
    db.add(
        AuditLog(
            workspace_id=workspace.id,
            action="INTEGRATION_CONNECTED",
            resource_type="INTEGRATION",
            resource_id=integration.id,
            details={"provider": "GMAIL", "account_email": integration.account_email},
        )
    )
    await db.commit()
    await db.refresh(integration)
    return IntegrationResponse(
        id=integration.id,
        workspace_id=integration.workspace_id,
        provider=integration.provider,
        is_connected=integration.is_connected,
        account_email=integration.account_email,
        status_message=integration.status_message,
        scopes=cred.scopes,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect integration, revoke Google OAuth credentials, and remove stored secrets."""
    res = await db.execute(
        select(Integration).where(Integration.id == integration_id, Integration.workspace_id == workspace.id)
    )
    integration = res.scalars().first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    cred_res = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id)
    )
    cred = cred_res.scalars().first()
    if cred:
        try:
            raw_token = decrypt_secret(cred.encrypted_token)
            await GmailService.revoke_token(raw_token)
        except Exception as exc:
            pass
        await db.delete(cred)

    integration.is_connected = False
    integration.account_email = None
    integration.status_message = "Disconnected"

    # Audit log
    db.add(
        AuditLog(
            workspace_id=workspace.id,
            action="INTEGRATION_DISCONNECTED",
            resource_type="INTEGRATION",
            resource_id=integration.id,
            details={"provider": integration.provider},
        )
    )
    await db.commit()
    return {"message": "Integration disconnected successfully and credentials revoked."}


@router.get("/gmail/authorize")
async def authorize_gmail(workspace: Workspace = Depends(get_current_workspace)):
    """Generate state token and redirect user to Google OAuth consent page."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.",
        )

    state = create_access_token(
        {"purpose": "gmail_oauth", "workspace_id": workspace.id},
        expires_delta=timedelta(minutes=10),
    )
    try:
        auth_url = GmailService.get_auth_url(state)
        return RedirectResponse(auth_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/gmail/callback")
async def gmail_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth 2.0 callback, validating cryptographic state and storing tokens."""
    claims = decode_access_token(state)
    if not claims or claims.get("purpose") != "gmail_oauth" or not claims.get("workspace_id"):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    workspace_id = claims["workspace_id"]

    try:
        token_response = await GmailService.exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google OAuth token exchange failed: {exc}") from exc

    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Google OAuth token exchange failed: no access token returned")

    result = await db.execute(
        select(Integration).where(Integration.workspace_id == workspace_id, Integration.provider == "GMAIL")
    )
    integration = result.scalars().first()
    if not integration:
        integration = Integration(workspace_id=workspace_id, provider="GMAIL")
        db.add(integration)
        await db.flush()

    cred_res = await db.execute(
        select(IntegrationCredential).where(IntegrationCredential.integration_id == integration.id)
    )
    cred = cred_res.scalars().first()
    expires_in = int(token_response.get("expires_in", 3600))
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if not cred:
        cred = IntegrationCredential(
            integration_id=integration.id,
            encrypted_token=encrypt_secret(access_token),
            encrypted_refresh_token=encrypt_secret(token_response["refresh_token"]) if token_response.get("refresh_token") else None,
            token_expiry=expiry,
            scopes=token_response.get("scope", "").split() or GMAIL_SCOPES,
        )
        db.add(cred)
    else:
        cred.encrypted_token = encrypt_secret(access_token)
        cred.token_expiry = expiry
        if token_response.get("refresh_token"):
            cred.encrypted_refresh_token = encrypt_secret(token_response["refresh_token"])
        cred.scopes = token_response.get("scope", "").split() or GMAIL_SCOPES

    integration.is_connected = True
    integration.account_email = token_response.get("email")
    integration.status_message = "Connected (OAuth Active)"

    db.add(
        AuditLog(
            workspace_id=workspace_id,
            action="INTEGRATION_CONNECTED",
            resource_type="INTEGRATION",
            resource_id=integration.id,
            details={"provider": "GMAIL", "account_email": integration.account_email},
        )
    )
    await db.commit()
    # Redirect to frontend integration page with success query param
    return RedirectResponse(url="http://localhost:3000/integrations?connected=gmail", status_code=status.HTTP_302_FOUND)


@router.get("/gmail/preview", response_model=GmailActionPreview)
async def preview_gmail_inbox(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Preview unread messages from the workspace's authorized Gmail account."""
    result = await db.execute(
        select(IntegrationCredential)
        .join(Integration, Integration.id == IntegrationCredential.integration_id)
        .where(
            Integration.workspace_id == workspace.id,
            Integration.provider == "GMAIL",
            Integration.is_connected.is_(True),
        )
    )
    credential = result.scalars().first()
    if not credential:
        raise HTTPException(
            status_code=409,
            detail="Gmail connection required: please connect Gmail in the Integration Hub before previewing messages.",
        )

    try:
        access_token = await _get_valid_access_token(credential, db)
        service = GmailService(access_token=access_token)
        unread = await service.fetch_unread_messages(max_results=5)
        return GmailActionPreview(unread_count=len(unread), sample_threads=unread)
    except Exception:
        return GmailActionPreview(unread_count=0, sample_threads=[])
