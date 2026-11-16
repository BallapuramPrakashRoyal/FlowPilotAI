from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AIConfigResponse(BaseModel):
    workspace_id: str
    default_provider: str
    default_model: str
    request_limit: int
    daily_token_limit: int
    sensitive_fields: List[str] = Field(default_factory=list)


class AIConfigUpdate(BaseModel):
    default_provider: str = Field(min_length=1, max_length=50)
    default_model: str = Field(min_length=1, max_length=150)
    api_key: Optional[str] = None
    request_limit: int = Field(default=100, ge=1, le=100000)
    daily_token_limit: int = Field(default=100000, ge=1, le=100000000)
    pricing: Dict[str, float] = Field(default_factory=dict)
    sensitive_fields: List[str] = Field(default_factory=list)
