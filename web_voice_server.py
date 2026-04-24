import os
import re
import string
import subprocess
import tempfile
import unicodedata
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from coreiot_rpc_controller import CoreIotRpcController

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
GENERATED_AUDIO_DIR = BASE_DIR / "generated_audio"
GENERATED_AUDIO_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Local Voice Smart Home Assistant")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/audio", StaticFiles(directory=GENERATED_AUDIO_DIR), name="audio")


class TextTurnRequest(BaseModel):
    text: str


class AssistantResult(BaseModel):
    transcript: str
    intent: str
    response_text: str
    audio_url: Optional[str] = None


class WhisperEngine:
    def __init__(self):
        if WhisperModel is None:
            raise RuntimeError("faster-whisper is not installed")

        model_size = os.getenv("WHISPER_MODEL_SIZE", "small")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self.language = os.getenv("WHISPER_LANGUAGE", "vi")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe_file(self, audio_path: str) -> str:
        segments, _ = self.model.transcribe(audio_path, language=self.language, beam_size=1)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text


_WHISPER_ENGINE: Optional[WhisperEngine] = None


def get_whisper_engine() -> WhisperEngine:
    global _WHISPER_ENGINE
    if _WHISPER_ENGINE is None:
        _WHISPER_ENGINE = WhisperEngine()
    return _WHISPER_ENGINE


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_intent(user_text: str) -> tuple[str, dict]:
    normalized = normalize_text(user_text)

    if not normalized:
        return "empty", {}

    if any(k in normalized for k in ["bat den", "mo den", "led on", "turn on led", "bat led"]):
        return "set_led", {"on": True}

    if any(k in normalized for k in ["tat den", "dong den", "led off", "turn off led", "tat led"]):
        return "set_led", {"on": False}

    if "servo" in normalized or "goc" in normalized or "quay" in normalized:
        match = re.search(r"(\d{1,3})", normalized)
        if not match:
            return "need_clarification", {"question": "Please provide a servo angle from 0 to 180."}
        angle = max(0, min(180, int(match.group(1))))
        return "set_servo", {"angle": angle}

    if any(k in normalized for k in ["nhiet do", "do am", "temperature", "humidity", "cam bien", "moi truong", "read sensor"]):
        if any(k in normalized for k in ["hom nay", "today", "tinh trang", "condition", "house status", "nha"]):
            return "house_summary", {}
        return "read_sensor", {}

    if any(k in normalized for k in ["tinh trang nha", "condition of the house", "house today", "nha hom nay"]):
        return "house_summary", {}

    return "out_of_domain", {}


def _to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def build_house_advice(temp_value, humidity_value) -> str:
    t = _to_float(temp_value)
    h = _to_float(humidity_value)

    if t is None and h is None:
        return "I cannot read current environment values right now."

    parts = []
    if t is not None:
        parts.append(f"It is {t:.1f} degrees Celsius")
    if h is not None:
        parts.append(f"with {h:.1f}% humidity")

    intro = ", ".join(parts)

    tips = []
    if t is not None:
        if t >= 35:
            tips.append("It feels very hot, so drink more water")
            tips.append("Wear cool and breathable clothes")
            tips.append("Avoid going outside unless needed")
        elif t >= 30:
            tips.append("It is warm, so stay hydrated")
            tips.append("Keep the room ventilated")
        elif t <= 20:
            tips.append("It feels cool, so keep yourself warm")

    if h is not None:
        if h < 35:
            tips.append("The air is dry, consider using a humidifier or drinking more water")
        elif h > 75:
            tips.append("Humidity is high, improve ventilation to stay comfortable")

    if not tips:
        tips.append("The environment looks comfortable now")

    tips_text = ". ".join(dict.fromkeys(tips))
    return f"{intro}. {tips_text}."


def run_piper_tts(text: str) -> Optional[str]:
    piper_path = os.getenv("PIPER_PATH", "piper")
    piper_model = os.getenv("PIPER_MODEL", "")

    if not piper_model:
        return None

    if not Path(piper_model).exists():
        return None

    output_name = f"reply_{uuid.uuid4().hex}.wav"
    output_path = GENERATED_AUDIO_DIR / output_name

    cmd = [piper_path, "--model", piper_model, "--output_file", str(output_path)]

    try:
        subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
    except Exception:
        return None

    return f"/audio/{output_name}"


def get_controller() -> CoreIotRpcController:
    email = os.getenv("COREIOT_EMAIL", "").strip()
    password = os.getenv("COREIOT_PASSWORD", "").strip()
    device_id = os.getenv("COREIOT_DEVICE_ID", "914ec000-24d4-11f1-8e7d-45cdb4e6c818").strip()

    if not email or not password:
        raise HTTPException(status_code=500, detail="COREIOT_EMAIL and COREIOT_PASSWORD are required")

    try:
        return CoreIotRpcController(email=email, password=password, device_id=device_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CoreIoT login failed: {exc}") from exc


def execute_user_text(user_text: str) -> AssistantResult:
    intent, payload = parse_intent(user_text)

    if intent == "empty":
        response_text = "I could not hear anything. Please try again."
        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    if intent == "out_of_domain":
        response_text = (
            "I can only help with smart-home tasks, such as reading temperature and humidity "
            "or controlling devices like LED and servo."
        )
        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    if intent == "need_clarification":
        response_text = payload["question"]
        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    controller = get_controller()

    if intent == "set_led":
        state = payload["on"]
        controller.set_led(state)
        response_text = "The LED is now on." if state else "The LED is now off."
        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    if intent == "set_servo":
        angle = payload["angle"]
        controller.set_servo(angle)
        response_text = f"Servo is set to {angle} degrees."
        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    if intent in {"read_sensor", "house_summary"}:
        sensor = controller.read_temp_humi()
        temp = sensor.get("temperature", "N/A")
        humi = sensor.get("humidity", "N/A")

        if intent == "house_summary":
            response_text = build_house_advice(temp, humi)
        else:
            response_text = f"Current temperature is {temp} degrees Celsius and humidity is {humi} percent."

        return AssistantResult(transcript=user_text, intent=intent, response_text=response_text, audio_url=run_piper_tts(response_text))

    response_text = "I could not understand your command."
    return AssistantResult(transcript=user_text, intent="unknown", response_text=response_text, audio_url=run_piper_tts(response_text))


@app.get("/")
def get_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "whisper_available": WhisperModel is not None,
        "piper_model_configured": bool(os.getenv("PIPER_MODEL", "")),
    }


@app.post("/api/text-turn", response_model=AssistantResult)
def text_turn(payload: TextTurnRequest):
    return execute_user_text(payload.text)


@app.post("/api/voice-turn", response_model=AssistantResult)
async def voice_turn(audio: UploadFile = File(...)):
    if WhisperModel is None:
        raise HTTPException(status_code=500, detail="faster-whisper is not installed")

    suffix = Path(audio.filename or "input.webm").suffix or ".webm"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(await audio.read())
        temp_audio_path = tmp_file.name

    try:
        whisper = get_whisper_engine()
        transcript = whisper.transcribe_file(temp_audio_path)
        return execute_user_text(transcript)
    finally:
        try:
            os.remove(temp_audio_path)
        except Exception:
            pass
