from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app

client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "clientflow-api"}


def test_readiness_check_returns_ready() -> None:
    db = Mock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    db.execute.assert_called_once()


def test_readiness_check_returns_503_when_database_fails() -> None:
    db = Mock(spec=Session)
    db.execute.side_effect = Exception("database connection failed")
    app.dependency_overrides[get_db] = lambda: db

    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "database connection failed" not in response.text
