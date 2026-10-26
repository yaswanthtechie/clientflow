import jwt


def test_auth_me_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_user_id_for_valid_token(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "me.user@example.com",
            "password": "password123",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "me.user@example.com",
            "password": "password123",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json()["user_id"], int)


def test_auth_me_rejects_garbage_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_auth_me_rejects_expired_token(client):
    expired_token = jwt.encode(
        {"sub": "1", "exp": 0},
        "test-only-secret-key-not-for-production",
        algorithm="HS256",
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
