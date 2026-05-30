import base64
import logging
import tempfile
from pathlib import Path
from typing import Generator, Optional

from fastapi import HTTPException

from backend.app.core.config import get_settings
from backend.app.core.audit import write_audit_event
from backend.app.db.repository import storage_repository
from backend.app.schemas.voice import AssistantResult
from backend.app.services.coreiot_service import coreiot_service
from backend.app.services.llm_service import decide_intent, generate_response_text, stream_response_text
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


class VoiceService:
    def _resolve_intent(self, user_text: str) -> tuple[str, dict, str]:
        if not user_text.strip():
            return "empty", {}, "local"

        settings = get_settings()
        if settings.llm_enabled and settings.llm_intent_enabled and settings.llm_backend.strip().lower() == "ollama":
            decision = decide_intent(user_text)
            if decision and decision.confidence >= settings.llm_confidence_threshold:
                intent = decision.intent
                params = decision.params or {}
                if intent == "set_led" and isinstance(params.get("on"), bool):
                    return intent, params, "llm"
                if intent == "set_servo":
                    angle = params.get("angle")
                    if isinstance(angle, (int, float)):
                        params["angle"] = max(0, min(180, int(angle)))
                        return intent, params, "llm"
                    return "need_clarification", {
                        "question": "Bạn muốn xoay servo tới góc bao nhiêu? Hãy nói một góc từ 0 đến 180, ví dụ: 'servo 90 độ'."
                    }, "llm"
                if intent == "device_status":
                    device = params.get("device")
                    if device not in {"led", "servo", "all"}:
                        params["device"] = "all"
                    return intent, params, "llm"
                if intent in {"read_sensor", "house_summary", "out_of_domain", "chitchat", "need_clarification"}:
                    return intent, params, "llm"
            return "need_clarification", {
                "question": (
                    "Bạn muốn tôi làm gì? Ví dụ: đọc nhiệt độ/độ ẩm, bật/tắt đèn, "
                    "hoặc xoay servo đến một góc cụ thể."
                )
            }, "llm_low_confidence"

        return "need_clarification", {
            "question": "Tôi chưa sẵn sàng xử lý lệnh lúc này. Bạn vui lòng thử lại sau ít phút."
        }, "llm_unavailable"

    def _build_response_text(self, user_text: str) -> tuple[str, str, str]:
        intent, payload, source = self._resolve_intent(user_text)
        logger.info("Voice intent resolved", extra={"intent": intent, "source": source})
        write_audit_event({
            "event": "intent_resolved",
            "intent": intent,
            "source": source,
            "user_text": user_text,
        })

        if intent == "empty":
            return (
                intent,
                f"Tôi chưa nghe rõ lệnh của bạn. Vui lòng thử lại. {VALID_COMMAND_HINT}",
                source,
            )

        if intent == "out_of_domain":
            return (
                intent,
                f"Tôi chỉ hỗ trợ các lệnh nhà thông minh như đọc nhiệt độ, độ ẩm, bật tắt LED hoặc điều khiển servo. {VALID_COMMAND_HINT}",
                source,
            )

        if intent == "chitchat":
            return intent, "Tôi sẵn sàng hỗ trợ các lệnh nhà thông minh. Bạn muốn làm gì tiếp?", source

        if intent == "device_status":
            try:
                status = coreiot_service.get_device_status()
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text, source

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

            return intent, ". ".join(parts) + ".", source

        if intent == "need_clarification":
            return intent, payload["question"], source

        if intent == "set_led":
            try:
                status = coreiot_service.set_led(bool(payload["on"]), source="voice")
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text, source
            state_text = "bật" if status.led_on else "tắt"
            logger.info("Device action executed", extra={"action": "set_led", "value": status.led_on})
            write_audit_event({
                "event": "device_action",
                "action": "set_led",
                "value": status.led_on,
                "intent": intent,
            })
            return intent, f"Đèn LED hiện đã {state_text}.", source

        if intent == "set_servo":
            try:
                status = coreiot_service.set_servo(int(payload["angle"]), source="voice")
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text, source
            angle = status.servo_angle if status.servo_angle is not None else int(payload["angle"])
            logger.info("Device action executed", extra={"action": "set_servo", "value": angle})
            write_audit_event({
                "event": "device_action",
                "action": "set_servo",
                "value": angle,
                "intent": intent,
            })
            return intent, f"Servo đã được đặt ở góc {angle} độ.", source

        if intent in {"read_sensor", "house_summary"}:
            try:
                snapshot = coreiot_service.get_latest_snapshot()
            except HTTPException as exc:
                return intent, self._coreiot_failure_result(user_text, intent, exc).response_text, source
            if intent == "house_summary":
                response_text = build_house_advice(snapshot.temperature, snapshot.humidity)
            else:
                sensor = (payload or {}).get("sensor", "all")
                if sensor == "temperature":
                    response_text = f"Nhiệt độ hiện tại là {snapshot.temperature} độ C."
                elif sensor == "humidity":
                    response_text = f"Độ ẩm hiện tại là {snapshot.humidity}%."
                else:
                    response_text = (
                        f"Nhiệt độ hiện tại là {snapshot.temperature} độ C "
                        f"và độ ẩm là {snapshot.humidity}%."
                    )
            return intent, response_text, source

        return "unknown", f"Tôi chưa hiểu lệnh của bạn. {VALID_COMMAND_HINT}", source

    def _coreiot_failure_result(self, user_text: str, intent: str, exc: Exception) -> AssistantResult:
        logger.warning("Voice command could not reach CoreIoT", exc_info=True)
        detail = getattr(exc, "detail", None)
        response_text = COREIOT_UNAVAILABLE_MESSAGE
        if detail:
            response_text = f"{response_text} Chi tiết: {detail}"
        return self._result(user_text, intent, response_text)

    def log_interaction(
        self,
        transcript: str,
        intent: str,
        response_text: str,
        *,
        success: bool = True,
    ) -> None:
        storage_repository.log_voice_interaction(
            transcript,
            intent,
            response_text,
            success=success,
        )

    def execute_text(self, user_text: str) -> AssistantResult:
        intent, response_text, _source = self._build_response_text(user_text)
        success = not response_text.startswith(COREIOT_UNAVAILABLE_MESSAGE)
        result = self._result(user_text, intent, response_text)
        self.log_interaction(user_text, intent, result.response_text, success=success)
        return result

    def stream_response(self, user_text: str) -> tuple[str, Generator[str, None, str]]:
        intent, response_text, _source = self._build_response_text(user_text)
        if intent in {"set_led", "set_servo", "device_status", "read_sensor", "house_summary", "need_clarification"}:
            def dummy_generator():
                yield response_text
                return response_text
            return intent, dummy_generator()
        return intent, stream_response_text(user_text, response_text)

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
        if intent in {"set_led", "set_servo", "device_status", "read_sensor", "house_summary", "need_clarification"}:
            natural_response = response_text
        else:
            natural_response = generate_response_text(transcript, response_text)
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
