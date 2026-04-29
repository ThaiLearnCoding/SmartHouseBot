import argparse
import json
import queue
import re
import string
import sys
import time
import unicodedata
import logging
from getpass import getpass
from typing import Optional

from coreiot_rpc_controller import CoreIotRpcController

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    from vosk import KaldiRecognizer, Model
    VOSK_AVAILABLE = True
except Exception:
    VOSK_AVAILABLE = False


def prompt_if_missing(value: Optional[str], label: str, secret: bool = False) -> str:
    if value:
        return value

    while True:
        entered = getpass(f"{label}: ") if secret else input(f"{label}: ")
        entered = entered.strip()
        if entered:
            return entered
        print(f"{label} is required")


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    )
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_command(text: str) -> tuple[str, dict]:
    normalized = normalize_text(text)

    if not normalized:
        return "unknown", {}

    if any(k in normalized for k in ["thoat", "exit", "quit", "dung", "tam biet"]):
        return "exit", {}

    if any(k in normalized for k in ["bat den", "mo den", "led on", "turn on led", "bat led"]):
        return "set_led", {"on": True}

    if any(k in normalized for k in ["tat den", "dong den", "led off", "turn off led", "tat led"]):
        return "set_led", {"on": False}

    if any(k in normalized for k in ["nhiet do", "do am", "temperature", "humidity", "cam bien", "moi truong", "read"]):
        return "read_sensor", {}

    if "servo" in normalized or "goc" in normalized or "quay" in normalized:
        match = re.search(r"(\d{1,3})", normalized)
        if match:
            angle = max(0, min(180, int(match.group(1))))
            return "set_servo", {"angle": angle}

    return "unknown", {}


def execute_command(controller: CoreIotRpcController, action: str, payload: dict) -> bool:
    if action == "exit":
        print("Exiting assistant")
        return False

    if action == "set_led":
        state = payload["on"]
        controller.set_led(state)
        print(f"Done: LED {'ON' if state else 'OFF'}")
        return True

    if action == "set_servo":
        angle = payload["angle"]
        controller.set_servo(angle)
        print(f"Done: Servo set to {angle} degree")
        return True

    if action == "read_sensor":
        result = controller.read_temp_humi()
        if result:
            temp = result.get("temperature", "N/A")
            humi = result.get("humidity", "N/A")
            print(f"Current sensor -> temperature={temp}, humidity={humi}")
        return True

    print("Could not understand command. Example: 'bat den', 'tat den', 'servo 90', 'doc nhiet do'")
    return True


class VoskMicListener:
    def __init__(self, model_path: str, sample_rate: int = 16000):
        self.model = Model(model_path)
        self.sample_rate = sample_rate
        self.audio_q: queue.Queue[bytes] = queue.Queue()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio warning: {status}")
        self.audio_q.put(bytes(indata))

    def listen_once(self, max_seconds: float = 8.0) -> str:
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        start = time.time()

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while time.time() - start < max_seconds:
                try:
                    data = self.audio_q.get(timeout=1.0)
                except queue.Empty:
                    continue

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        return text

        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "").strip()


def run_text_loop(controller: CoreIotRpcController):
    print("Text mode ready. Type command or 'exit'")
    while True:
        user_text = input("You: ").strip()
        action, payload = parse_command(user_text)
        keep_running = execute_command(controller, action, payload)
        if not keep_running:
            return


def run_voice_loop(controller: CoreIotRpcController, model_path: str):
    if not VOSK_AVAILABLE:
        print("Voice dependencies are missing. Falling back to text mode.")
        print("Install with: pip install vosk sounddevice")
        run_text_loop(controller)
        return

    try:
        listener = VoskMicListener(model_path=model_path)
    except Exception as exc:
        logger.error(f"Could not load Vosk model at '{model_path}'", exc_info=True)
        print("Falling back to text mode.")
        run_text_loop(controller)
        return

    print("Voice mode ready. Speak your command in Vietnamese. Say 'thoat' to exit.")
    while True:
        print("Listening...")
        heard = listener.listen_once(max_seconds=8.0)
        if not heard:
            print("No speech recognized. Please try again.")
            continue

        print(f"Heard: {heard}")
        action, payload = parse_command(heard)
        keep_running = execute_command(controller, action, payload)
        if not keep_running:
            return


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Local voice assistant for CoreIoT smart home")
    parser.add_argument("--email", help="CoreIoT email")
    parser.add_argument("--password", help="CoreIoT password")
    parser.add_argument(
        "--device-id",
        default="914ec000-24d4-11f1-8e7d-45cdb4e6c818",
        help="Target device ID",
    )
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="voice",
        help="Assistant input mode",
    )
    parser.add_argument(
        "--vosk-model",
        default="models/vosk-model-small-vn-0.4",
        help="Path to local Vosk Vietnamese model",
    )

    args = parser.parse_args()

    email = prompt_if_missing(args.email, "CoreIoT email")
    password = prompt_if_missing(args.password, "CoreIoT password", secret=True)

    try:
        controller = CoreIotRpcController(email=email, password=password, device_id=args.device_id)
    except Exception as exc:
        logger.error("Failed to initialize CoreIoT controller", exc_info=True)
        sys.exit(1)

    if args.mode == "voice":
        run_voice_loop(controller, model_path=args.vosk_model)
    else:
        run_text_loop(controller)


if __name__ == "__main__":
    main()
