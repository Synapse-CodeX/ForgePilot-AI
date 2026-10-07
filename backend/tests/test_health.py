from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root API endpoint."""

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "ForgePilot AI"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health_endpoint() -> None:
    """Test the health API endpoint."""

    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "ForgePilot AI"
