import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(autouse=True)
def setup_database():
    import app.models  # noqa: F401 - registers User on Base.metadata

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_register_returns_created_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "new.user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.user@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email_same_case(client):
    first = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    assert first.status_code == 201

    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )

    assert response.status_code == 409


def test_register_rejects_duplicate_email_different_case(client):
    first = client.post(
        "/auth/register",
        json={"email": "Case@Example.com", "password": "password123"},
    )
    assert first.status_code == 201

    response = client.post(
        "/auth/register",
        json={"email": "case@example.com", "password": "password123"},
    )

    assert response.status_code == 409


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_register_rejects_long_email(client):
    long_local = "a" * 250

    response = client.post(
        "/auth/register",
        json={
            "email": f"{long_local}@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422
