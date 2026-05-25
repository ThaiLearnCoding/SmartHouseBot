import logging
import uuid
import wave
from pathlib import Path
from typing import Optional

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)

try:
    from piper.voice import PiperVoice
except Exception as exc:  # pragma: no cover - dependency may be absent locally
    PiperVoice = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class TtsService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._voice: Optional[PiperVoice] = None

    @property
    def available(self) -> bool:
        return PiperVoice is not None and bool(self.settings.piper_model)

    def _get_voice(self) -> PiperVoice:
        if PiperVoice is None:
            raise RuntimeError(f"piper-tts is unavailable: {IMPORT_ERROR}")

        model_path = Path(self.settings.piper_model)
        if not model_path.exists():
            raise RuntimeError(f"Piper model was not found at {model_path}")

        if self._voice is None:
            self._voice = PiperVoice.load(str(model_path))
        return self._voice

    def synthesize(self, text: str) -> Optional[str]:
        if not text.strip():
            text = "I did not catch that."

        try:
            output_name = f"reply_{uuid.uuid4().hex}.wav"
            output_path = self.settings.generated_audio_dir / output_name
            voice = self._get_voice()
            with wave.open(str(output_path), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
            if output_path.stat().st_size <= 44:
                output_path.unlink(missing_ok=True)
                raise RuntimeError("Piper produced an empty WAV file.")
            return f"/audio/{output_name}"
        except Exception:
            logger.error("Piper synthesis failed", exc_info=True)
            return None


tts_service = TtsService()
