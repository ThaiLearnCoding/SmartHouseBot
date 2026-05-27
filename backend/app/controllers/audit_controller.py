from backend.app.db.repository import storage_repository
from backend.app.schemas.audit import DeviceCommandLogList, VoiceLogList


def get_device_command_logs(limit: int, offset: int) -> DeviceCommandLogList:
    items, total = storage_repository.list_device_commands(limit=limit, offset=offset)
    return DeviceCommandLogList(items=items, total=total)


def get_voice_logs(limit: int, offset: int) -> VoiceLogList:
    items, total = storage_repository.list_voice_logs(limit=limit, offset=offset)
    return VoiceLogList(items=items, total=total)
