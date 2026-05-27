from typing import Dict

from pydantic import BaseModel, Field


class LlmDecision(BaseModel):
    intent: str
    params: Dict = Field(default_factory=dict)
    confidence: float = 0.0
