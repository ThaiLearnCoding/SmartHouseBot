from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.services.tts_service import tts_service
from backend.app.services.whisper_service import whisper_service


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "whisper_available": whisper_service.available,
        "whisper_warmup_state": whisper_service.warmup_state,
        "whisper_warmup_error": whisper_service.warmup_error,
        "piper_model_configured": bool(settings.piper_model),
        "tts_available": tts_service.available,
        "llm_enabled": settings.llm_enabled,
        "llm_backend": settings.llm_backend,
        "ollama_model": settings.ollama_model,
    }
