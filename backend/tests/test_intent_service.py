from backend.app.services.intent_service import normalize_text, parse_intent


def test_normalize_text_converts_vietnamese_d():
    assert normalize_text("Bật đèn") == "bat den"
    assert normalize_text("đọc nhiệt độ độ ẩm") == "doc nhiet do do am"


def test_parse_vietnamese_device_and_sensor_commands():
    assert parse_intent("bật đèn") == ("set_led", {"on": True})
    assert parse_intent("tắt đèn") == ("set_led", {"on": False})
    assert parse_intent("servo 90 độ") == ("set_servo", {"angle": 90})
    assert parse_intent("đọc nhiệt độ độ ẩm") == ("read_sensor", {"sensor": "all"})
    assert parse_intent("đọc nhiệt độ") == ("read_sensor", {"sensor": "temperature"})
    assert parse_intent("đọc độ ẩm") == ("read_sensor", {"sensor": "humidity"})
