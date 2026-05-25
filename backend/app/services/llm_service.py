import json
import logging
from typing import Optional

import requests

from backend.app.core.config import get_settings
from backend.app.schemas.llm import LlmDecision


logger = logging.getLogger(__name__)

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


def _build_intent_prompt(user_text: str) -> str:
    return (
        "Bạn là bộ phân tích ý định cho trợ lý nhà thông minh. "
        "Trả về JSON duy nhất với các trường: intent, params, confidence. "
        "Không thêm giải thích, không thêm Markdown. "
        "intent chỉ được là một trong: "
        "set_led, set_servo, device_status, read_sensor, house_summary, need_clarification, out_of_domain, chitchat. "
        "params phải là object JSON, dùng các khóa sau: "
        "set_led -> {\"on\": true|false}; set_servo -> {\"angle\": 0..180}. "
        "device_status -> {\"device\": \"led\"|\"servo\"|\"all\"} (tuỳ chọn, mặc định all). "
        "Nếu thiếu thông tin cho servo, dùng intent=need_clarification và params chứa {\"question\": ...}. "
        "confidence là số từ 0 đến 1.\n\n"
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

    try:
        response = requests.post(
            f"{settings.ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        data = json.loads(raw)
        decision = LlmDecision.model_validate(data)
        if decision.intent not in ALLOWED_INTENTS:
            return None
        return decision
    except Exception:
        logger.error("LLM intent decision failed", exc_info=True)
        return None
