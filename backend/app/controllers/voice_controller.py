from backend.app.schemas.voice import AssistantResult
from backend.app.services.voice_service import voice_service


def process_text_turn(text: str) -> AssistantResult:
    return voice_service.execute_text(text)


def process_audio_turn(suffix: str, content: bytes) -> AssistantResult:
    return voice_service.execute_audio(suffix=suffix, content=content)


def process_audio_transcribe(suffix: str, content: bytes) -> str:
    return voice_service.transcribe_audio(suffix=suffix, content=content)
