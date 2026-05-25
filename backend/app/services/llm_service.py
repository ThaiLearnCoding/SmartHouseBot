import json
import logging
from typing import Generator, Optional

import requests

from backend.app.core.config import get_settings
from backend.app.schemas.llm import LlmDecision


logger = logging.getLogger(__name__)

_last_llm_decision = {
    "intent": None,
    "confidence": None,
    "source": None,
    "error": None,
}


def get_last_llm_decision() -> dict:
    return dict(_last_llm_decision)

NATURAL_RESPONSE_SYSTEM = (
    "Bạn là trợ lý nhà thông minh. QUY TẮC TỐI THƯỢNG: Chỉ được phép trả lời bằng TIẾNG VIỆT (Vietnamese). "
    "Tuyệt đối KHÔNG sử dụng tiếng Trung, tiếng Anh, tiếng Indonesia hay bất kỳ ngôn ngữ nào khác. "
    "Nhiệm vụ: Viết lại câu trả lời gốc sao cho tự nhiên, thân thiện và dễ hiểu. "
    "Phải giữ nguyên chính xác các thông số (nhiệt độ, độ ẩm, góc servo, trạng thái bật/tắt). "
    "Chỉ trả về nội dung câu trả lời cuối cùng, không giải thích gì thêm."
)

ALLOWED_INTENTS = {
    "set_led",
    "set_servo",
    "device_status",
    "read_sensor",
    "house_summary",
    "need_clarification",
    "out_of_domain",
    "chitchat",
}


def _request_ollama(payload: dict) -> str:
    settings = get_settings()
    response = requests.post(
        f"{settings.ollama_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=settings.llm_timeout_seconds,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def _repair_intent_json(raw: str, user_text: str) -> Optional[dict]:
    settings = get_settings()
    if not raw:
        return None

    prompt = (
        "Hãy chuyển nội dung sau thành JSON hợp lệ cho intent. "
        "Chỉ trả về JSON, không thêm giải thích. "
        "Schema: {intent, params, confidence}. "
        f"Câu lệnh: {user_text}\n"
        f"Nội dung: {raw}\nJSON:"
    )

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }

    try:
        fixed = _request_ollama(payload)
        return json.loads(fixed)
    except Exception:
        logger.error("LLM intent JSON repair failed", exc_info=True)
        return None


def _build_intent_prompt(user_text: str) -> str:
    return (
        "Bạn là bộ chọn công cụ cho trợ lý nhà thông minh. "
        "Trả về JSON duy nhất với các trường: intent, params, confidence. "
        "Không thêm giải thích, không thêm Markdown. "
        "intent chính là tên công cụ cần dùng và chỉ được là một trong: "
        "set_led, set_servo, device_status, read_sensor, house_summary, need_clarification, out_of_domain, chitchat. "
        "params phải là object JSON, dùng các khóa sau: "
        "set_led -> {\"on\": true|false}; set_servo -> {\"angle\": 0..180}. "
        "device_status -> {\"device\": \"led\"|\"servo\"|\"all\"} (tuỳ chọn, mặc định all). "
        "Nếu thiếu thông tin cho servo, dùng intent=need_clarification và params chứa {\"question\": ...}. "
        "confidence là số từ 0 đến 1.\n\n"
        "Ví dụ:\n"
        "- Câu lệnh: 'nhiệt độ hiện tại là bao nhiêu' -> {\"intent\": \"read_sensor\", \"params\": {}, \"confidence\": 0.9}\n"
        "- Câu lệnh: 'trời nóng quá, nhiệt độ bao nhiêu vậy' -> {\"intent\": \"read_sensor\", \"params\": {}, \"confidence\": 0.9}\n"
        "- Câu lệnh: 'độ ẩm hiện tại bao nhiêu' -> {\"intent\": \"read_sensor\", \"params\": {}, \"confidence\": 0.9}\n"
        "- Câu lệnh: 'trạng thái đèn LED' -> {\"intent\": \"device_status\", \"params\": {\"device\": \"led\"}, \"confidence\": 0.9}\n\n"
        f"Câu lệnh: {user_text}\n"
        "JSON:"
    )


def decide_intent(user_text: str) -> Optional[LlmDecision]:
    settings = get_settings()
    if not settings.llm_enabled or settings.llm_backend.strip().lower() != "ollama":
        return None

    payload = {
        "model": settings.ollama_model,
        "prompt": _build_intent_prompt(user_text),
        "stream": False,
        "options": {
            "temperature": 0.0,
        },
    }

    raw = None
    try:
        raw = _request_ollama(payload)
        data = json.loads(raw)
    except Exception:
        logger.warning("LLM intent JSON parse failed, attempting repair", exc_info=True)
        data = _repair_intent_json(raw or "", user_text)

    if not data:
        _last_llm_decision.update({"intent": None, "confidence": None, "source": "llm", "error": "parse_failed"})
        return None

    try:
        decision = LlmDecision.model_validate(data)
    except Exception:
        logger.error("LLM intent validation failed", exc_info=True)
        _last_llm_decision.update({"intent": None, "confidence": None, "source": "llm", "error": "validation_failed"})
        return None

    if decision.intent not in ALLOWED_INTENTS:
        _last_llm_decision.update({"intent": decision.intent, "confidence": decision.confidence, "source": "llm", "error": "invalid_intent"})
        return None
    _last_llm_decision.update({"intent": decision.intent, "confidence": decision.confidence, "source": "llm", "error": None})
    return decision


def generate_response_text(user_text: str, base_response: str) -> str:
    settings = get_settings()
    if not settings.llm_enabled or settings.llm_backend.strip().lower() != "ollama":
        return base_response

    prompt = (
        f"Lệnh của người dùng: {user_text}\n"
        f"Câu trả lời gốc: {base_response}\n\n"
        "Hãy viết lại câu trả lời gốc bằng TIẾNG VIỆT:"
    )

    payload = {
        "model": settings.ollama_model,
        "system": NATURAL_RESPONSE_SYSTEM,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.5,
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


def stream_response_text(user_text: str, base_response: str) -> Generator[str, None, str]:
    settings = get_settings()
    if not settings.llm_enabled or settings.llm_backend.strip().lower() != "ollama":
        yield base_response
        return base_response

    prompt = (
        f"Lệnh của người dùng: {user_text}\n"
        f"Câu trả lời gốc: {base_response}\n\n"
        "Hãy viết lại câu trả lời gốc bằng TIẾNG VIỆT:"
    )

    payload = {
        "model": settings.ollama_model,
        "system": NATURAL_RESPONSE_SYSTEM,
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
