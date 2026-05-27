from typing import Optional

from pydantic import BaseModel


class TextTurnRequest(BaseModel):
    text: str


class AssistantResult(BaseModel):
    transcript: str
    intent: str
    response_text: str
    audio_url: Optional[str] = None


class TranscriptionResult(BaseModel):
    transcript: str
