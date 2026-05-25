import base64
import json
import logging
import tempfile
from pathlib import Path
from typing import Generator, Optional

import requests
from fastapi import HTTPException

from backend.app.core.config import get_settings
from backend.app.schemas.voice import AssistantResult
from backend.app.services.coreiot_service import coreiot_service
from backend.app.services.intent_service import parse_intent
from backend.app.services.llm_service import decide_intent
from backend.app.services.tts_service import tts_service
from backend.app.services.whisper_service import whisper_service


logger = logging.getLogger(__name__)

VALID_COMMAND_HINT = (
    "Bạn có thể nói: 'bật đèn', 'tắt đèn', 'servo 90 độ', "
    "'đọc nhiệt độ độ ẩm', hoặc 'tình trạng nhà hôm nay'."
)

COREIOT_UNAVAILABLE_MESSAGE = (
    "Tôi đã hiểu lệnh của bạn, nhưng hiện tại chưa gửi được yêu cầu tới CoreIOT. "
    "CoreIOT có thể đang phản hồi chậm hoặc thiết bị đang mất kết nối. "
    "Bạn vui lòng thử lại sau vài giây."
)


def _to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def build_house_advice(temp_value, humidity_value) -> str:
    temp = _to_float(temp_value)
    humidity = _to_float(humidity_value)

    if temp is None and humidity is None:
        return f"Hiện tại tôi chưa đọc được nhiệt độ và độ ẩm. {VALID_COMMAND_HINT}"

    parts = []
    if temp is not None:
        parts.append(f"Nhiệt độ hiện tại là {temp:.1f} độ C")
    if humidity is not None:
        parts.append(f"độ ẩm là {humidity:.1f}%")

    tips = []
    if temp is not None:
        if temp >= 35:
            tips.extend(
                [
                    "Trời đang rất nóng, bạn nên uống thêm nước",
                    "Nên mặc đồ thoáng mát",
                    "Hạn chế ra ngoài nếu không cần thiết",
                ]
            )
        elif temp >= 30:
            tips.extend(["Thời tiết khá nóng, bạn nên uống đủ nước", "Nên giữ phòng thông thoáng"])
        elif temp <= 20:
            tips.append("Thời tiết hơi lạnh, bạn nên giữ ấm")

    if humidity is not None:
        if humidity < 35:
            tips.append("Không khí đang khô, bạn có thể dùng máy tạo ẩm hoặc uống thêm nước")
        elif humidity > 75:
            tips.append("Độ ẩm đang cao, nên tăng thông gió để dễ chịu hơn")

    if not tips:
        tips.append("Môi trường hiện tại khá dễ chịu")

    intro = ", ".join(parts)
    tips_text = ". ".join(dict.fromkeys(tips))
    return f"{intro}. {tips_text}."


def maybe_natural_response(intent: str, user_text: str, base_response: str) -> str:
    settings = get_settings()
    if not settings.llm_enabled or settings.llm_backend.strip().lower() != "ollama":
        return base_response

    system_prompt = (
        "Bạn là trợ lý nhà thông minh. QUY TẮC TỐI THƯỢNG: Chỉ được phép trả lời bằng TIẾNG VIỆT (Vietnamese). "
        "Tuyệt đối KHÔNG sử dụng tiếng Trung, tiếng Anh, tiếng Indonesia hay bất kỳ ngôn ngữ nào khác. "
        "Nhiệm vụ: Viết lại câu trả lời gốc sao cho tự nhiên, thân thiện và dễ hiểu. "
        "Phải giữ nguyên chính xác các thông số (nhiệt độ, độ ẩm, góc servo, trạng thái bật/tắt). "
        "Chỉ trả về nội dung câu trả lời cuối cùng, không giải thích gì thêm."
    )

    prompt = (
        f"Lệnh của người dùng: {user_text}\n"
        f"Câu trả lời gốc: {base_response}\n\n"
        "Hãy viết lại câu trả lời gốc bằng TIẾNG VIỆT:"
    )

    payload = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lowered to heavily reduce hallucinations
            "top_p": 0.5
        },
    }

    try:
        response = requests.post(
            f"{settings.ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        candidate = response.json().get("response", "").strip()
        return candidate or base_response
    except Exception:
        logger.error("Failed to call LLM backend", exc_info=True)
        return base_response


def stream_natural_response(
    intent: str,
    user_text: str,
    base_response: str,
) -> Generator[str, None, str]:
    settings = get_settings()
    if not settings.llm_enabled or settings.llm_backend.strip().lower() != "ollama":
        yield base_response
        return base_response

    system_prompt = (
        "Bạn là trợ lý nhà thông minh. QUY TẮC TỐI THƯỢNG: Chỉ được phép trả lời bằng TIẾNG VIỆT (Vietnamese). "
        "Tuyệt đối KHÔNG sử dụng tiếng Trung, tiếng Anh, tiếng Indonesia hay bất kỳ ngôn ngữ nào khác. "
        "Nhiệm vụ: Viết lại câu trả lời gốc sao cho tự nhiên, thân thiện và dễ hiểu. "
        "Phải giữ nguyên chính xác các thông số (nhiệt độ, độ ẩm, góc servo, trạng thái bật/tắt). "
        "Chỉ trả về nội dung câu trả lời cuối cùng, không giải thích gì thêm."
    )

    prompt = (
        f"Lệnh của người dùng: {user_text}\n"
        f"Câu trả lời gốc: {base_response}\n\n"
        "Hãy viết lại câu trả lời gốc bằng TIẾNG VIỆT:"
    )

    payload = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "top_p": 0.5,
        },
    }

    final_text = ""
    try:
        with requests.post(
            f"{settings.ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=settings.llm_timeout_seconds,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    final_text += token
                    yield token
                if data.get("done"):
                    break
    except Exception:
        logger.error("Failed to stream LLM backend", exc_info=True)
        if not final_text:
            yield base_response
            return base_response

    return final_text.strip() or base_response


class VoiceService:
    def _looks_like_status_query(self, user_text: str) -> bool:
        normalized = user_text.lower()
        return any(key in normalized for key in [
            "trang thai",
            "hien tai",
            "dang the nao",
            "dang ra sao",
            "bat hay tat",
            "bao nhieu",
        ])

    def _resolve_intent(self, user_text: str) -> tuple[str, dict]:
        settings = get_settings()
        if settings.llm_enabled and settings.llm_intent_enabled and settings.llm_backend.strip().lower() == "ollama":
            decision = decide_intent(user_text)
            if decision and decision.confidence >= settings.llm_confidence_threshold:
                intent = decision.intent
                params = decision.params or {}
                if intent in {"set_led", "set_servo"} and self._looks_like_status_query(user_text):
                    return "device_status", {"device": "all"}
                if intent == "set_led" and isinstance(params.get("on"), bool):
                    return intent, params
                if intent == "set_servo":
                    angle = params.get("angle")
                    if isinstance(angle, (int, float)):
                        params["angle"] = max(0, min(180, int(angle)))
                        return intent, params
                    return "need_clarification", {
                        "question": "Bạn muốn xoay servo tới góc bao nhiêu? Hãy nói một góc từ 0 đến 180, ví dụ: 'servo 90 độ'."
                    }
                if intent == "device_status":
                    device = params.get("device")
                    if device not in {"led", "servo", "all"}:
                        params["device"] = "all"
                    return intent, params
                if intent in {"read_sensor", "house_summary", "out_of_domain", "chitchat", "need_clarification"}:
                    return intent, params

        return parse_intent(user_text)

    def _build_response_text(self, user_text: str) -> tuple[str, str]:
        intent, payload = self._resolve_intent(user_text)

        if intent == "empty":
            return (
                intent,
                f"Tôi chưa nghe rõ lệnh của bạn. Vui lòng thử lại. {VALID_COMMAND_HINT}",
            )

        if intent == "out_of_domain":
            return (
                intent,
                f"Tôi chỉ hỗ trợ các lệnh nhà thông minh như đọc nhiệt độ, độ ẩm, bật tắt LED hoặc điều khiển servo. {VALID_COMMAND_HINT}",
            )

        if intent == "chitchat":
            return intent, "Tôi sẵn sàng hỗ trợ các lệnh nhà thông minh. Bạn muốn làm gì tiếp?"

        if intent == "device_status":
            try:
                status = coreiot_service.get_device_status()
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text

            device = (payload or {}).get("device", "all")
            parts = []
            if device in {"led", "all"}:
                if status.led_on is None:
                    parts.append("Tôi chưa đọc được trạng thái đèn LED")
                else:
                    parts.append(f"Đèn LED hiện đang {'bật' if status.led_on else 'tắt'}")
            if device in {"servo", "all"}:
                if status.servo_angle is None:
                    parts.append("Tôi chưa đọc được góc servo hiện tại")
                else:
                    parts.append(f"Servo hiện ở góc {status.servo_angle} độ")

            return intent, ". ".join(parts) + "."

        if intent == "need_clarification":
            return intent, payload["question"]

        if intent == "set_led":
            try:
                status = coreiot_service.set_led(bool(payload["on"]))
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text
            state_text = "bật" if status.led_on else "tắt"
            return intent, f"Đèn LED hiện đã {state_text}."

        if intent == "set_servo":
            try:
                status = coreiot_service.set_servo(int(payload["angle"]))
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text
            angle = status.servo_angle if status.servo_angle is not None else int(payload["angle"])
            return intent, f"Servo đã được đặt ở góc {angle} độ."

        if intent in {"read_sensor", "house_summary"}:
            try:
                snapshot = coreiot_service.get_latest_snapshot()
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text
            if intent == "house_summary":
                response_text = build_house_advice(snapshot.temperature, snapshot.humidity)
            else:
                response_text = (
                    f"Nhiệt độ hiện tại là {snapshot.temperature} độ C "
                    f"và độ ẩm là {snapshot.humidity}%."
                )
            return intent, response_text

        return "unknown", f"Tôi chưa hiểu lệnh của bạn. {VALID_COMMAND_HINT}"

    def _coreiot_failure_result(self, user_text: str, intent: str, exc: Exception) -> AssistantResult:
        logger.warning("Voice command could not reach CoreIoT", exc_info=True)
        detail = getattr(exc, "detail", None)
        response_text = COREIOT_UNAVAILABLE_MESSAGE
        if detail:
            response_text = f"{response_text} Chi tiết: {detail}"
        return self._result(user_text, intent, response_text)

    def execute_text(self, user_text: str) -> AssistantResult:
        intent, response_text = self._build_response_text(user_text)
        return self._result(user_text, intent, response_text)

    def stream_response(self, user_text: str) -> tuple[str, Generator[str, None, str]]:
        intent, response_text = self._build_response_text(user_text)
        return intent, stream_natural_response(intent, user_text, response_text)

    def execute_audio(self, suffix: str, content: bytes) -> AssistantResult:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".webm") as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        try:
            transcript = whisper_service.transcribe_file(temp_path)
            result = self.execute_text(transcript)
            result.transcript = transcript
            return result
        finally:
            temp_path.unlink(missing_ok=True)

    def transcribe_audio(self, suffix: str, content: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".webm") as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        try:
            return whisper_service.transcribe_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def _result(self, transcript: str, intent: str, response_text: str) -> AssistantResult:
        natural_response = maybe_natural_response(intent, transcript, response_text)
        return AssistantResult(
            transcript=transcript,
            intent=intent,
            response_text=natural_response,
            audio_url=tts_service.synthesize(natural_response),
        )

    def synthesize_audio_chunks(self, text: str) -> Optional[list[str]]:
        chunks = tts_service.synthesize_chunks(text)
        if not chunks:
            return None
        return [base64.b64encode(chunk).decode("ascii") for chunk in chunks]


voice_service = VoiceService()
