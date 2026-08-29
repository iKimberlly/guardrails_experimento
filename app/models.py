from typing import Literal, Optional
from pydantic import BaseModel, Field

Mode = Literal["regex", "agent", "combined"]

class ValidationRequest(BaseModel):
    prompt: str = Field(min_length=1)

class ValidationResponse(BaseModel):
    approved: bool
    mode: Mode
    layer: str
    reasons: list[str] = []
    sanitized_prompt: str = ""
    matched_rules: list[str] = []
    latency_ms: float
    agent_model: Optional[str] = None
