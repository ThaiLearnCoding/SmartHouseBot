import io
import logging
import time
import uuid
import wave
from pathlib import Path
from typing import Optional

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)

_AUDIO_TTL_SECONDS = 3600

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

    def cleanup_old_files(self, max_age_seconds: int = _AUDIO_TTL_SECONDS) -> None:
        output_dir = self.settings.generated_audio_dir
        cutoff = time.time() - max_age_seconds
        for path in output_dir.glob("reply_*.wav"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to delete stale audio file %s", path, exc_info=True)

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
            self.cleanup_old_files()
            return f"/audio/{output_name}"
        except Exception:
            logger.error("Piper synthesis failed", exc_info=True)
            return None

    def synthesize_chunks(self, text: str, chunk_seconds: float = 0.6) -> Optional[list[bytes]]:
        if not text.strip():
            text = "I did not catch that."

        try:
            voice = self._get_voice()
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

            buffer.seek(0)
            with wave.open(buffer, "rb") as wav_reader:
                params = wav_reader.getparams()
                sample_rate = wav_reader.getframerate()
                frames_per_chunk = max(1, int(sample_rate * chunk_seconds))
                chunks: list[bytes] = []

                while True:
                    frames = wav_reader.readframes(frames_per_chunk)
                    if not frames:
                        break

                    chunk_buffer = io.BytesIO()
                    with wave.open(chunk_buffer, "wb") as chunk_writer:
                        chunk_writer.setnchannels(params.nchannels)
                        chunk_writer.setsampwidth(params.sampwidth)
                        chunk_writer.setframerate(params.framerate)
                        chunk_writer.writeframes(frames)

                    chunks.append(chunk_buffer.getvalue())

            return chunks
        except Exception:
            logger.error("Piper chunked synthesis failed", exc_info=True)
            return None


tts_service = TtsService()
