import logging
import tempfile
from pathlib import Path

import requests
from fastapi import HTTPException

from backend.app.core.config import get_settings
from backend.app.schemas.voice import AssistantResult
from backend.app.services.coreiot_service import coreiot_service
from backend.app.services.intent_service import parse_intent
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


class VoiceService:
    def _coreiot_failure_result(self, user_text: str, intent: str, exc: Exception) -> AssistantResult:
        logger.warning("Voice command could not reach CoreIoT", exc_info=True)
        detail = getattr(exc, "detail", None)
        response_text = COREIOT_UNAVAILABLE_MESSAGE
        if detail:
            response_text = f"{response_text} Chi tiết: {detail}"
        return self._result(user_text, intent, response_text)

    def execute_text(self, user_text: str) -> AssistantResult:
        intent, payload = parse_intent(user_text)

        if intent == "empty":
            return self._result(
                user_text,
                intent,
                f"Tôi chưa nghe rõ lệnh của bạn. Vui lòng thử lại. {VALID_COMMAND_HINT}",
            )

        if intent == "out_of_domain":
            return self._result(
                user_text,
                intent,
                f"Tôi chỉ hỗ trợ các lệnh nhà thông minh như đọc nhiệt độ, độ ẩm, bật tắt LED hoặc điều khiển servo. {VALID_COMMAND_HINT}",
            )

        if intent == "need_clarification":
            return self._result(user_text, intent, payload["question"])

        if intent == "set_led":
            try:
                status = coreiot_service.set_led(bool(payload["on"]))
            except HTTPException as exc:
                return self._coreiot_failure_result(user_text, intent, exc)
            state_text = "bật" if status.led_on else "tắt"
            return self._result(user_text, intent, f"Đèn LED hiện đã {state_text}.")

        if intent == "set_servo":
            try:
                status = coreiot_service.set_servo(int(payload["angle"]))
            except HTTPException as exc:
                return self._coreiot_failure_result(user_text, intent, exc)
            angle = status.servo_angle if status.servo_angle is not None else int(payload["angle"])
            return self._result(user_text, intent, f"Servo đã được đặt ở góc {angle} độ.")

        if intent in {"read_sensor", "house_summary"}:
            try:
                snapshot = coreiot_service.get_latest_snapshot()
            except HTTPException as exc:
                return self._coreiot_failure_result(user_text, intent, exc)
            if intent == "house_summary":
                response_text = build_house_advice(snapshot.temperature, snapshot.humidity)
            else:
                response_text = (
                    f"Nhiệt độ hiện tại là {snapshot.temperature} độ C "
                    f"và độ ẩm là {snapshot.humidity}%."
                )
            return self._result(user_text, intent, response_text)

        return self._result(user_text, "unknown", f"Tôi chưa hiểu lệnh của bạn. {VALID_COMMAND_HINT}")

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

    def _result(self, transcript: str, intent: str, response_text: str) -> AssistantResult:
        natural_response = maybe_natural_response(intent, transcript, response_text)
        return AssistantResult(
            transcript=transcript,
            intent=intent,
            response_text=natural_response,
            audio_url=tts_service.synthesize(natural_response),
        )


voice_service = VoiceService()
