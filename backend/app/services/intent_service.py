import re
import string
import unicodedata
from typing import Dict, Tuple


def normalize_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = normalized.replace("đ", "d")
    normalized = "".join(
        ch for ch in unicodedata.normalize("NFD", normalized) if unicodedata.category(ch) != "Mn"
    )
    normalized = normalized.translate(str.maketrans("", "", string.punctuation))
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def parse_intent(user_text: str) -> Tuple[str, Dict]:
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
            return "need_clarification", {
                "question": "Bạn muốn xoay servo tới góc bao nhiêu? Hãy nói một góc từ 0 đến 180, ví dụ: 'servo 90 độ'."
            }
        return "set_servo", {"angle": max(0, min(180, int(match.group(1))))}

    if any(k in normalized for k in ["nhiet do", "do am", "temperature", "humidity", "cam bien", "read sensor"]):
        if any(k in normalized for k in ["hom nay", "today", "tinh trang", "condition", "house status", "nha"]):
            return "house_summary", {}
        return "read_sensor", {}

    if any(k in normalized for k in ["tinh trang nha", "condition of the house", "house today", "nha hom nay"]):
        return "house_summary", {}

    return "out_of_domain", {}
