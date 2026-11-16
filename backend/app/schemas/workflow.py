"""Pydantic schemas for Workflows and Node Graphs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WorkflowNodeSchema(BaseModel):
    id: str
    type: str  # e.g., "manualTrigger", "aiAgent", "humanApproval", "gmailTrigger"
    label: str
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class WorkflowGraphSchema(BaseModel):
    nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    edges: List[WorkflowEdgeSchema] = Field(default_factory=list)
    viewport: Optional[Dict[str, Any]] = None


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    workspace_id: str
    graph: Optional[WorkflowGraphSchema] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    graph: Optional[WorkflowGraphSchema] = None
    changelog: Optional[str] = None
    is_published: Optional[bool] = None


class WorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version_number: int
    graph_data: WorkflowGraphSchema
    is_published: bool
    changelog: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    current_version_id: Optional[str] = None
    graph: Optional[WorkflowGraphSchema] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowGenerateRequest(BaseModel):
    workspace_id: Optional[str] = None
    prompt: str = Field(min_length=5, description="Natural language description of desired workflow")


class WorkflowGenerateResponse(BaseModel):
    name: str
    description: str
    explanation: str
    suggested_integrations: List[str]
    graph: WorkflowGraphSchema


class WorkflowValidateResponse(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)


class WorkflowPublishRequest(BaseModel):
    changelog: Optional[str] = None
