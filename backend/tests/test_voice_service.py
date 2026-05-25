from types import SimpleNamespace

from fastapi import HTTPException

from backend.app.schemas.llm import LlmDecision
from backend.app.services.voice_service import VALID_COMMAND_HINT, voice_service


def test_invalid_voice_command_returns_vietnamese_recommendations(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )

    result = voice_service.execute_text("play music")

    assert result.intent == "out_of_domain"
    assert "Tôi chỉ hỗ trợ" in result.response_text
    assert VALID_COMMAND_HINT in result.response_text
    assert "bật đèn" in result.response_text
    assert "servo 90 độ" in result.response_text


def test_led_command_returns_vietnamese_response(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )
    monkeypatch.setattr(
        "backend.app.services.voice_service.coreiot_service",
        SimpleNamespace(set_led=lambda on: SimpleNamespace(led_on=on)),
    )

    result = voice_service.execute_text("bat den")

    assert result.intent == "set_led"
    assert result.response_text == "Đèn LED hiện đã bật."


def test_vietnamese_sensor_command_returns_current_values(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )
    monkeypatch.setattr(
        "backend.app.services.voice_service.coreiot_service",
        SimpleNamespace(
            get_latest_snapshot=lambda: SimpleNamespace(temperature=32.56, humidity=62.51)
        ),
    )

    result = voice_service.execute_text("đọc nhiệt độ độ ẩm")

    assert result.intent == "read_sensor"
    assert result.response_text == "Nhiệt độ hiện tại là 32.56 độ C và độ ẩm là 62.51%."


def test_coreiot_timeout_returns_assistant_message_instead_of_raising(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )

    def fail_servo(_angle):
        raise HTTPException(status_code=502, detail="CoreIoT servo command failed: timed out")

    monkeypatch.setattr(
        "backend.app.services.voice_service.coreiot_service",
        SimpleNamespace(set_servo=fail_servo),
    )

    result = voice_service.execute_text("servo 90")

    assert result.intent == "set_servo"
    assert "Tôi đã hiểu lệnh của bạn" in result.response_text
    assert "CoreIOT" in result.response_text
    assert "timed out" in result.response_text


def test_status_query_returns_device_status(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )
    monkeypatch.setattr(
        "backend.app.services.voice_service.coreiot_service",
        SimpleNamespace(get_device_status=lambda: SimpleNamespace(led_on=True, servo_angle=45)),
    )

    result = voice_service.execute_text("trang thai den led hien tai")

    assert result.intent == "device_status"
    assert "Đèn LED" in result.response_text
    assert "bật" in result.response_text


def test_llm_low_confidence_falls_back_to_rule_parser(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )
    monkeypatch.setattr(
        "backend.app.services.voice_service.decide_intent",
        lambda text: LlmDecision(intent="set_led", params={"on": True}, confidence=0.1),
    )
    monkeypatch.setattr(
        "backend.app.services.voice_service.coreiot_service",
        SimpleNamespace(set_led=lambda on: SimpleNamespace(led_on=on)),
    )

    result = voice_service.execute_text("bat den")

    assert result.intent == "set_led"
    assert result.response_text == "Đèn LED hiện đã bật."


def test_llm_repair_attempt_falls_back_when_invalid(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.voice_service.tts_service",
        SimpleNamespace(synthesize=lambda text: None),
    )
    monkeypatch.setattr(
        "backend.app.services.llm_service._request_ollama",
        lambda payload: "not json",
    )
    monkeypatch.setattr(
        "backend.app.services.llm_service._repair_intent_json",
        lambda raw, text: None,
    )

    result = voice_service.execute_text("bat den")

    assert result.intent in {"set_led", "out_of_domain", "unknown"}
