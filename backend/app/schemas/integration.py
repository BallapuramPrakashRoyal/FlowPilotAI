"""Pydantic schemas for Integrations and Analytics."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class IntegrationResponse(BaseModel):
    id: str
    workspace_id: str
    provider: str
    is_connected: bool
    account_email: Optional[str] = None
    status_message: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntegrationConnectRequest(BaseModel):
    workspace_id: str
    provider: str
    auth_code: Optional[str] = None
    mock_mode: Optional[bool] = False


class GmailActionPreview(BaseModel):
    unread_count: int
    sample_threads: List[Dict[str, Any]] = Field(default_factory=list)


# Analytics
class TrendItem(BaseModel):
    date: str
    executions: int
    successes: int
    failures: int


class AnalyticsOverviewResponse(BaseModel):
    total_workflows: int
    active_workflows: int
    total_executions: int = 0
    successful_executions: int
    failed_executions: int
    success_rate_percent: float = 0.0
    failure_rate_percent: float = 0.0
    pending_approvals: int
    avg_duration_ms: float
    total_tokens_consumed: int
    estimated_cost_usd: float
    connected_integrations_count: int = 0
    connected_integrations: List[Dict[str, Any]] = Field(default_factory=list)
    recent_agent_runs: List[Dict[str, Any]] = Field(default_factory=list)
    recent_audit_logs: List[Dict[str, Any]] = Field(default_factory=list)
    execution_trends: List[TrendItem] = Field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
