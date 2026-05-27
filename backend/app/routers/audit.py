from fastapi import APIRouter, Query

from backend.app.controllers.audit_controller import get_device_command_logs, get_voice_logs
from backend.app.schemas.audit import DeviceCommandLogList, VoiceLogList


router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/commands", response_model=DeviceCommandLogList)
def read_device_commands(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return get_device_command_logs(limit, offset)


@router.get("/voice", response_model=VoiceLogList)
def read_voice_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return get_voice_logs(limit, offset)
