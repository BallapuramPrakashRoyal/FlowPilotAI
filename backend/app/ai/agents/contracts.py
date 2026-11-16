"""Typed contracts shared by the controlled multi-agent orchestrator."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class AgentTask(BaseModel):
    task_id: str
    agent: str
    objective: str
    depends_on: List[str] = Field(default_factory=list)
    input: Dict[str, Any] = Field(default_factory=dict)
    sensitive: bool = False


class AgentHandoff(BaseModel):
    from_agent: str
    to_agent: str
    task_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "COMPLETED"


class AgentFinding(BaseModel):
    name: str
    value: Any
    confidence: float = Field(default=1.0, ge=0, le=1)
    evidence: List[str] = Field(default_factory=list)


class PlanResult(BaseModel):
    tasks: List[AgentTask]
    tools: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    is_valid: bool
    findings: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
