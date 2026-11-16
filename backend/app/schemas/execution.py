"""Pydantic schemas for Execution Engine and Approvals."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ExecutionCreate(BaseModel):
    workflow_id: str
    workflow_version_id: Optional[str] = None
    trigger_type: str = "MANUAL"
    context_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutionNodeResponse(BaseModel):
    id: str
    node_id: str
    node_type: str
    status: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int

    model_config = ConfigDict(from_attributes=True)


class ExecutionEventResponse(BaseModel):
    id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionResponse(BaseModel):
    id: str
    workspace_id: str
    workflow_id: str
    workflow_version_id: str
    status: str
    trigger_type: str
    context_data: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    token_usage: Dict[str, Any]
    nodes: List[ExecutionNodeResponse] = Field(default_factory=list)
    events: List[ExecutionEventResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(description="'APPROVED' or 'REJECTED'")
    decision_notes: Optional[str] = None
    edited_proposal: Optional[Dict[str, Any]] = None


class ApprovalResponse(BaseModel):
    id: str
    workspace_id: str
    execution_id: str
    execution_node_id: str
    action_type: str
    title: str
    proposal_data: Dict[str, Any]
    status: str
    decided_by: Optional[str] = None
    decision_notes: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
