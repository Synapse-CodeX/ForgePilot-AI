"""Tests for the ForgePilot API foundation."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root API endpoint."""

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "ForgePilot AI",
        "version": "0.1.0",
        "status": "running",
    }


def test_health_endpoint() -> None:
    """Test the health API endpoint."""

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ForgePilot AI",
    }


def test_not_found_returns_standard_error() -> None:
    """Test that missing routes return a consistent error format."""

    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "http_error",
            "message": "Not Found",
        }
    }
