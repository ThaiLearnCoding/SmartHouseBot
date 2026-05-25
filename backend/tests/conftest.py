from fastapi.testclient import TestClient
import pytest

from backend.app.core.rate_limit import rate_limiter
from backend.app.main import app


@pytest.fixture(autouse=True)
def clear_rate_limits():
    rate_limiter._hits.clear()
    yield
    rate_limiter._hits.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
