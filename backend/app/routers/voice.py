from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile

from backend.app.controllers.voice_controller import process_audio_turn, process_text_turn
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import build_rate_limit_key, rate_limiter
from backend.app.schemas.voice import AssistantResult, TextTurnRequest


router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/text-turn", response_model=AssistantResult)
def text_turn(payload: TextTurnRequest, request: Request):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "voice-text"),
        settings.voice_rate_limit_count,
        settings.voice_rate_limit_window_seconds,
    )
    return process_text_turn(payload.text)


@router.post("/audio-turn", response_model=AssistantResult)
async def audio_turn(request: Request, audio: UploadFile = File(...)):
    settings = get_settings()
    rate_limiter.enforce(
        build_rate_limit_key(request, "voice-audio"),
        settings.voice_rate_limit_count,
        settings.voice_rate_limit_window_seconds,
    )
    suffix = Path(audio.filename or "input.webm").suffix or ".webm"
    content = await audio.read()
    return process_audio_turn(suffix=suffix, content=content)
