from backend.app.db.repository import storage_repository


def test_list_device_commands_and_voice_logs():
    storage_repository.log_device_command("led", {"on": True}, source="web", success=True)
    storage_repository.log_device_command("servo", {"angle": 45}, source="voice", success=False)
    storage_repository.log_voice_interaction(
        "bat den",
        "set_led",
        "Den LED hien da bat.",
        success=True,
    )

    commands, command_total = storage_repository.list_device_commands(limit=10)
    voice_logs, voice_total = storage_repository.list_voice_logs(limit=10)

    assert command_total >= 2
    assert voice_total >= 1
    assert commands[0].command_type in {"led", "servo"}
    assert commands[0].payload in ({"on": True}, {"angle": 45})
    assert voice_logs[0].transcript == "bat den"
    assert voice_logs[0].intent == "set_led"


def test_audit_api_returns_logs(client):
    storage_repository.log_device_command("led", {"on": False}, source="web", success=True)
    storage_repository.log_voice_interaction("doc nhiet do", "read_sensor", "28 do C", success=True)

    commands_response = client.get("/api/audit/commands?limit=10")
    voice_response = client.get("/api/audit/voice?limit=10")

    assert commands_response.status_code == 200
    assert voice_response.status_code == 200

    commands_body = commands_response.json()
    voice_body = voice_response.json()

    assert commands_body["total"] >= 1
    assert len(commands_body["items"]) >= 1
    assert commands_body["items"][0]["command_type"] == "led"

    assert voice_body["total"] >= 1
    assert len(voice_body["items"]) >= 1
    assert voice_body["items"][0]["intent"] == "read_sensor"
