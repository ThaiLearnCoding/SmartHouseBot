from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Smart Home Dashboard API"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    client_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    serve_frontend: bool = True

    coreiot_email: str = Field(default="", alias="COREIOT_EMAIL")
    coreiot_password: str = Field(default="", alias="COREIOT_PASSWORD")
    coreiot_device_id: str = Field(
        default="914ec000-24d4-11f1-8e7d-45cdb4e6c818",
        alias="COREIOT_DEVICE_ID",
    )
    coreiot_base_url: str = Field(default="http://app.coreiot.io", alias="COREIOT_BASE_URL")
    coreiot_timeout_seconds: float = Field(default=10.0, alias="COREIOT_TIMEOUT_SECONDS")

    whisper_model_size: str = Field(default="small", alias="WHISPER_MODEL_SIZE")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    whisper_compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    whisper_language: str = Field(default="vi", alias="WHISPER_LANGUAGE")

    pho_whisper_model: str = Field(default="", alias="PHO_WHISPER_MODEL")
    pho_whisper_device: str = Field(default="auto", alias="PHO_WHISPER_DEVICE")
    pho_whisper_dtype: str = Field(default="float16", alias="PHO_WHISPER_DTYPE")
    pho_whisper_warmup: bool = Field(default=True, alias="PHO_WHISPER_WARMUP")
    hf_token: str = Field(default="", alias="HF_TOKEN")
    hf_home: str = Field(default="", alias="HF_HOME")
    hf_hub_offline: bool = Field(default=False, alias="HF_HUB_OFFLINE")
    transformers_offline: bool = Field(default=False, alias="TRANSFORMERS_OFFLINE")
    hf_disable_safetensors_conversion: bool = Field(
        default=False,
        alias="HF_HUB_DISABLE_SAFETENSORS_CONVERSION",
    )

    piper_model: str = Field(default="", alias="PIPER_MODEL")

    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    llm_backend: str = Field(default="ollama", alias="LLM_BACKEND")
    ollama_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="qwen2.5:3b-instruct", alias="OLLAMA_MODEL")
    llm_temperature: float = Field(default=0.8, alias="LLM_TEMPERATURE")
    llm_timeout_seconds: float = Field(default=15.0, alias="LLM_TIMEOUT_SECONDS")
    llm_intent_enabled: bool = Field(default=True, alias="LLM_INTENT_ENABLED")
    llm_confidence_threshold: float = Field(default=0.6, alias="LLM_CONFIDENCE_THRESHOLD")
    audit_log_enabled: bool = Field(default=True, alias="AUDIT_LOG_ENABLED")
    audit_log_path: str = Field(default="backend/logs/audit.jsonl", alias="AUDIT_LOG_PATH")

    voice_rate_limit_count: int = Field(default=10, alias="VOICE_RATE_LIMIT_COUNT")
    voice_rate_limit_window_seconds: int = Field(default=60, alias="VOICE_RATE_LIMIT_WINDOW_SECONDS")
    device_rate_limit_count: int = Field(default=20, alias="DEVICE_RATE_LIMIT_COUNT")
    device_rate_limit_window_seconds: int = Field(default=60, alias="DEVICE_RATE_LIMIT_WINDOW_SECONDS")

    telemetry_default_hours: int = Field(default=24, alias="TELEMETRY_DEFAULT_HOURS")
    telemetry_max_hours: int = Field(default=72, alias="TELEMETRY_MAX_HOURS")
    telemetry_limit_points: int = Field(default=288, alias="TELEMETRY_LIMIT_POINTS")
    telemetry_device_keys: str = Field(
        default="temperature,humidity,ledState,servoAngle",
        alias="TELEMETRY_DEVICE_KEYS",
    )

    def get_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_telemetry_keys(self) -> List[str]:
        return [key.strip() for key in self.telemetry_device_keys.split(",") if key.strip()]

    def get_pho_whisper_model_id(self) -> str:
        if self.pho_whisper_model.strip():
            return self.pho_whisper_model.strip()

        size = self.whisper_model_size.strip().lower()
        size_map = {"tiny", "base", "small", "medium", "large"}
        if size in size_map:
            return f"vinai/PhoWhisper-{size}"

        return "vinai/PhoWhisper-small"

    @property
    def frontend_dist_dir(self) -> Path:
        return BASE_DIR / "frontend" / "dist"

    @property
    def generated_audio_dir(self) -> Path:
        path = BASE_DIR / "backend" / "generated_audio"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
