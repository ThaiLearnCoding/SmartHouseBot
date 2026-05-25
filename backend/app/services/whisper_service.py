import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import pipeline
except Exception as exc:  # pragma: no cover - dependency may be absent locally
    torch = None
    pipeline = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class WhisperService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._pipeline = None
        self._warmup_state = "idle"
        self._warmup_error: Optional[str] = None

    @property
    def available(self) -> bool:
        return pipeline is not None and torch is not None

    @property
    def warmup_state(self) -> str:
        return self._warmup_state

    @property
    def warmup_error(self) -> Optional[str]:
        return self._warmup_error

    def _get_pipeline(self):
        if pipeline is None or torch is None:
            raise HTTPException(status_code=500, detail=f"PhoWhisper is unavailable: {IMPORT_ERROR}")

        if self._pipeline is None:
            if self.settings.hf_hub_offline and not os.environ.get("HF_HUB_OFFLINE"):
                os.environ["HF_HUB_OFFLINE"] = "1"
            if self.settings.transformers_offline and not os.environ.get("TRANSFORMERS_OFFLINE"):
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
            if (
                self.settings.hf_disable_safetensors_conversion
                and not os.environ.get("HF_HUB_DISABLE_SAFETENSORS_CONVERSION")
            ):
                os.environ["HF_HUB_DISABLE_SAFETENSORS_CONVERSION"] = "1"
            if self.settings.hf_home.strip() and not os.environ.get("HF_HOME"):
                os.environ["HF_HOME"] = self.settings.hf_home.strip()
            if self.settings.hf_token.strip() and not os.environ.get("HF_TOKEN"):
                os.environ["HF_TOKEN"] = self.settings.hf_token.strip()
            model_id = self.settings.get_pho_whisper_model_id()
            device_setting = self.settings.pho_whisper_device.strip().lower()
            use_cuda = device_setting in {"cuda", "gpu", "auto"} and torch.cuda.is_available()
            device = 0 if use_cuda else -1
            dtype_setting = self.settings.pho_whisper_dtype.strip().lower()
            torch_dtype = torch.float16 if use_cuda and dtype_setting == "float16" else torch.float32
            self._pipeline = pipeline(
                "automatic-speech-recognition",
                model=model_id,
                device=device,
                dtype=torch_dtype,
            )
        return self._pipeline

    def warmup(self) -> None:
        self._warmup_state = "running"
        self._warmup_error = None
        try:
            self._get_pipeline()
            self._warmup_state = "ready"
        except Exception as exc:
            self._warmup_state = "failed"
            self._warmup_error = str(exc)
            raise

    def transcribe_file(self, audio_path: Path) -> str:
        asr = self._get_pipeline()
        result = asr(str(audio_path))
        if isinstance(result, dict):
            text = result.get("text", "")
        else:
            text = str(result)
        return text.strip()


whisper_service = WhisperService()
