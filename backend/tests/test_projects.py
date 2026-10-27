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

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_client(client, headers, name="Test Client"):
    response = client.post(
        "/clients",
        headers=headers,
        json={
            "name": name,
            "email": None,
            "hourly_rate_cents": 5000,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_project(client, headers, client_id, name="Test Project"):
    return client.post(
        "/projects",
        headers=headers,
        json={"client_id": client_id, "name": name},
    )


def test_create_project_requires_authentication(client):
    response = client.post(
        "/projects",
        json={"client_id": 1, "name": "Unauthorized Project"},
    )
    assert response.status_code == 401


def test_create_and_list_projects_under_own_client(client):
    headers = register_and_login(client, "project-owner@example.com")
    client_id = create_client(client, headers)

    created = create_project(client, headers, client_id)
    assert created.status_code == 201, created.text

    project = created.json()
    assert project["client_id"] == client_id
    assert project["name"] == "Test Project"
    assert project["status"] == "active"
    project_id = project["id"]

    listed = client.get(
        "/projects",
        headers=headers,
        params={"client_id": client_id},
    )
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == project_id


def test_cannot_create_project_under_another_users_client(client):
    user_a = register_and_login(client, "project-user-a@example.com")
    user_b = register_and_login(client, "project-user-b@example.com")
    client_id = create_client(client, user_a, name="Private Client")

    response = create_project(client, user_b, client_id)
    assert response.status_code == 404


def test_cannot_list_projects_for_another_users_client(client):
    user_a = register_and_login(client, "list-user-a@example.com")
    user_b = register_and_login(client, "list-user-b@example.com")
    client_id = create_client(client, user_a)

    response = client.get(
        "/projects",
        headers=user_b,
        params={"client_id": client_id},
    )
    assert response.status_code == 404


def test_owner_can_update_project_status_to_archived(client):
    headers = register_and_login(client, "archive-owner@example.com")
    client_id = create_client(client, headers)
    created = create_project(client, headers, client_id)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    updated = client.patch(
        f"/projects/{project_id}",
        headers=headers,
        json={"status": "archived"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "archived"

    fetched = client.get(f"/projects/{project_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "archived"


def test_owner_can_delete_project(client):
    headers = register_and_login(client, "delete-owner@example.com")
    client_id = create_client(client, headers)
    created = create_project(client, headers, client_id)
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    deleted = client.delete(f"/projects/{project_id}", headers=headers)
    assert deleted.status_code == 204

    fetched = client.get(f"/projects/{project_id}", headers=headers)
    assert fetched.status_code == 404


def test_other_user_cannot_get_update_or_delete_project(client):
    user_a = register_and_login(client, "private-project-owner@example.com")
    user_b = register_and_login(client, "private-project-visitor@example.com")
    client_id = create_client(client, user_a, name="Owner Client")

    created = create_project(client, user_a, client_id, name="Private Project")
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    assert client.get(
        f"/projects/{project_id}", headers=user_b
    ).status_code == 404

    assert client.patch(
        f"/projects/{project_id}",
        headers=user_b,
        json={"name": "Unauthorized Rename"},
    ).status_code == 404

    assert client.delete(
        f"/projects/{project_id}", headers=user_b
    ).status_code == 404

    # Verify the owner still has access and the project was not modified.
    owner_result = client.get(
        f"/projects/{project_id}", headers=user_a
    )
    assert owner_result.status_code == 200
    assert owner_result.json()["name"] == "Private Project"
