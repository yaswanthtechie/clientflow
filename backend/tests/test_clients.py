def register_and_login(client, email):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "TestPassword123!"},
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "TestPassword123!"},
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_client(client, headers, name="Test Client", rate=5000):
    return client.post(
        "/clients",
        headers=headers,
        json={
            "name": name,
            "email": None,
            "hourly_rate_cents": rate,
        },
    )


def test_create_client_requires_authentication(client):
    response = client.post(
        "/clients",
        json={"name": "Client A", "hourly_rate_cents": 5000},
    )
    assert response.status_code == 401


def test_create_list_get_update_delete_client(client):
    headers = register_and_login(client, "owner@example.com")

    created = create_client(client, headers)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["name"] == "Test Client"
    assert data["hourly_rate_cents"] == 5000
    client_id = data["id"]

    listed = client.get("/clients", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == client_id

    fetched = client.get(f"/clients/{client_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == client_id

    updated = client.patch(
        f"/clients/{client_id}",
        headers=headers,
        json={"name": "Updated Client", "hourly_rate_cents": 7500},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Updated Client"
    assert updated.json()["hourly_rate_cents"] == 7500

    deleted = client.delete(f"/clients/{client_id}", headers=headers)
    assert deleted.status_code == 204

    fetched_again = client.get(f"/clients/{client_id}", headers=headers)
    assert fetched_again.status_code == 404


def test_users_only_see_their_own_clients(client):
    user_a = register_and_login(client, "user-a@example.com")
    user_b = register_and_login(client, "user-b@example.com")

    created = create_client(client, user_a, name="Private Client")
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]

    listed = client.get("/clients", headers=user_b)
    assert listed.status_code == 200
    assert listed.json() == []

    assert client.get(
        f"/clients/{client_id}", headers=user_b
    ).status_code == 404

    assert client.patch(
        f"/clients/{client_id}",
        headers=user_b,
        json={"name": "Unauthorized Change"},
    ).status_code == 404

    assert client.delete(
        f"/clients/{client_id}", headers=user_b
    ).status_code == 404

    owner_result = client.get(f"/clients/{client_id}", headers=user_a)
    assert owner_result.status_code == 200
    assert owner_result.json()["name"] == "Private Client"


def test_negative_hourly_rate_is_rejected(client):
    headers = register_and_login(client, "rates@example.com")

    response = create_client(client, headers, rate=-1)
    assert response.status_code == 422
