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


def create_client(client, headers, name="Task Test Client"):
    response = client.post(
        "/clients",
        headers=headers,
        json={"name": name, "email": None, "hourly_rate_cents": 5000},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_project(client, headers, client_id, name="Task Test Project"):
    response = client.post(
        "/projects",
        headers=headers,
        json={"client_id": client_id, "name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create_task(client, headers, project_id, title="Prepare proposal"):
    return client.post(
        "/tasks",
        headers=headers,
        json={"project_id": project_id, "title": title},
    )


def test_create_list_get_update_and_delete_task(client):
    headers = register_and_login(client, "task-crud-owner@example.com")
    client_id = create_client(client, headers)
    project_id = create_project(client, headers, client_id)

    created = create_task(client, headers, project_id)
    assert created.status_code == 201, created.text
    task = created.json()
    task_id = task["id"]

    assert task["project_id"] == project_id
    assert task["title"] == "Prepare proposal"
    assert task["status"] == "open"
    assert "created_at" in task

    listed = client.get(
        "/tasks", headers=headers, params={"project_id": project_id}
    )
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == task_id for item in listed.json())

    fetched = client.get(f"/tasks/{task_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["id"] == task_id

    updated = client.patch(
        f"/tasks/{task_id}", headers=headers, json={"status": "done"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "done"
    assert updated.json()["id"] == task_id

    # Marking a task done must not delete the task itself.
    fetched_again = client.get(f"/tasks/{task_id}", headers=headers)
    assert fetched_again.status_code == 200
    assert fetched_again.json()["status"] == "done"

    deleted = client.delete(f"/tasks/{task_id}", headers=headers)
    assert deleted.status_code == 204

    missing = client.get(f"/tasks/{task_id}", headers=headers)
    assert missing.status_code == 404


def test_create_task_requires_authentication(client):
    response = client.post(
        "/tasks", json={"project_id": 1, "title": "Private task"}
    )
    assert response.status_code == 401


def test_cannot_create_task_under_another_users_project(client):
    owner = register_and_login(client, "task-project-owner@example.com")
    visitor = register_and_login(client, "task-project-visitor@example.com")

    client_id = create_client(client, owner)
    project_id = create_project(client, owner, client_id)

    response = create_task(client, visitor, project_id)
    assert response.status_code == 404


def test_cannot_list_tasks_for_another_users_project(client):
    owner = register_and_login(client, "task-list-owner@example.com")
    visitor = register_and_login(client, "task-list-visitor@example.com")

    client_id = create_client(client, owner)
    project_id = create_project(client, owner, client_id)

    response = client.get(
        "/tasks", headers=visitor, params={"project_id": project_id}
    )
    assert response.status_code == 404


def test_other_user_cannot_get_update_or_delete_task(client):
    owner = register_and_login(client, "task-private-owner@example.com")
    visitor = register_and_login(client, "task-private-visitor@example.com")

    client_id = create_client(client, owner)
    project_id = create_project(client, owner, client_id)
    created = create_task(client, owner, project_id, "Confidential task")
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]

    assert client.get(
        f"/tasks/{task_id}", headers=visitor
    ).status_code == 404

    assert client.patch(
        f"/tasks/{task_id}",
        headers=visitor,
        json={"status": "done"},
    ).status_code == 404

    assert client.delete(
        f"/tasks/{task_id}", headers=visitor
    ).status_code == 404

    # Owner's task must remain unchanged.
    owner_result = client.get(f"/tasks/{task_id}", headers=owner)
    assert owner_result.status_code == 200
    assert owner_result.json()["title"] == "Confidential task"
    assert owner_result.json()["status"] == "open"


def test_task_rejects_invalid_status_and_null_updates(client):
    headers = register_and_login(client, "task-validation-owner@example.com")
    client_id = create_client(client, headers)
    project_id = create_project(client, headers, client_id)
    created = create_task(client, headers, project_id)
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]

    invalid_status = client.patch(
        f"/tasks/{task_id}", headers=headers, json={"status": "in_progress"}
    )
    assert invalid_status.status_code == 422

    null_status = client.patch(
        f"/tasks/{task_id}", headers=headers, json={"status": None}
    )
    assert null_status.status_code == 422

    null_title = client.patch(
        f"/tasks/{task_id}", headers=headers, json={"title": None}
    )
    assert null_title.status_code == 422
