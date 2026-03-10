import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.main import app


def test_monitoring_endpoints() -> None:
    client = TestClient(app)
    assert client.get('/monitoring/health').status_code == 200
    assert 'agents' in client.get('/monitoring/metrics').json()
    assert 'features' in client.get('/monitoring/world_map').json()
    assert 'items' in client.get('/monitoring/logs').json()
