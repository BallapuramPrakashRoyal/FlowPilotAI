"""FlowPilot AI — FastAPI Backend Application Entrypoint."""

import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.database import check_database_health
from app.database.init_db import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.executions import router as executions_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.knowledge_bases import router as knowledge_bases_router
from app.api.v1.ai import router as ai_router
from app.api.v1.agents import router as agents_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flowpilot")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.scheme == "https" or settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and seed demo workspace
    logger.info("Initializing FlowPilot AI Backend Services...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Error during database startup initialization: {e}")
    yield
    logger.info("FlowPilot AI services shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Workflow Automation Platform with Multi-Agent Runtime and DAG Engine",
    lifespan=lifespan,
)

# Security Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(workspaces_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(executions_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(integrations_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(knowledge_bases_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "mode": "production-ready",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe verifying operational database and cache connections."""
    from fastapi.responses import JSONResponse
    db_health = await check_database_health()
    redis_healthy = False
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        redis_healthy = bool(await r.ping())
        await r.aclose()
    except Exception:
        redis_healthy = False

    is_ready = db_health.get("healthy", False)
    payload = {
        "status": "ready" if is_ready else "degraded",
        "database": db_health,
        "redis": {"healthy": redis_healthy},
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
    return JSONResponse(status_code=200 if is_ready else 503, content=payload)


# WebSocket Manager for Real-Time Execution Streaming
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, execution_id: str, websocket: WebSocket):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
        self.active_connections[execution_id].append(websocket)

    def disconnect(self, execution_id: str, websocket: WebSocket):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].remove(websocket)

    async def broadcast_event(self, execution_id: str, data: dict):
        if execution_id in self.active_connections:
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(data)
                except Exception:
                    pass


ws_manager = ConnectionManager()


@app.websocket("/api/v1/executions/{execution_id}/stream")
async def websocket_execution_stream(websocket: WebSocket, execution_id: str):
    await ws_manager.connect(execution_id, websocket)
    try:
        while True:
            # Keep-alive heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(execution_id, websocket)
