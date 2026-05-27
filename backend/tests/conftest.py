from fastapi.testclient import TestClient
import pytest

from backend.app.core.config import get_settings
from backend.app.core.rate_limit import rate_limiter
from backend.app.db.database import init_db, reset_connection
from backend.app.main import app


@pytest.fixture(autouse=True)
def clear_rate_limits():
    rate_limiter._hits.clear()
    yield
    rate_limiter._hits.clear()


from backend.app.core.config import get_settings


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("DATABASE_ENABLED", "true")
    monkeypatch.setenv("DATABASE_TELEMETRY_SAMPLER_ENABLED", "false")
    monkeypatch.setenv("PHO_WHISPER_WARMUP", "false")
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_INTENT_ENABLED", "false")
    get_settings.cache_clear()
    reset_connection()
    init_db()
    yield
    reset_connection()
    get_settings.cache_clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
