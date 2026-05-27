from typing import Any, List

from pydantic import BaseModel, Field


class DeviceCommandLog(BaseModel):
    id: int
    device_id: str
    command_type: str
    payload: dict[str, Any]
    source: str
    success: bool
    created_at: str


class VoiceLogEntry(BaseModel):
    id: int
    transcript: str
    intent: str
    response_text: str
    success: bool
    created_at: str


class DeviceCommandLogList(BaseModel):
    items: List[DeviceCommandLog] = Field(default_factory=list)
    total: int = 0


class VoiceLogList(BaseModel):
    items: List[VoiceLogEntry] = Field(default_factory=list)
    total: int = 0
