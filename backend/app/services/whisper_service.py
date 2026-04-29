import logging
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
except Exception as exc:  # pragma: no cover - dependency may be absent locally
    WhisperModel = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class WhisperService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model: Optional[WhisperModel] = None

    @property
    def available(self) -> bool:
        return WhisperModel is not None

    def _get_model(self) -> WhisperModel:
        if WhisperModel is None:
            raise HTTPException(status_code=500, detail=f"faster-whisper is unavailable: {IMPORT_ERROR}")

        if self._model is None:
            self._model = WhisperModel(
                self.settings.whisper_model_size,
                device=self.settings.whisper_device,
                compute_type=self.settings.whisper_compute_type,
            )
        return self._model

    def transcribe_file(self, audio_path: Path) -> str:
        model = self._get_model()
        segments, _ = model.transcribe(
            str(audio_path),
            language=self.settings.whisper_language,
            beam_size=1,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()


whisper_service = WhisperService()
