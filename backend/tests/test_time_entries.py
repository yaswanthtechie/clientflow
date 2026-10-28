from datetime import date

from conftest import TestingSessionLocal

from tests.test_tasks import (
    create_client,
    create_project,
    create_task,
    register_and_login,
)


def create_time_entry(client, headers, task_id, minutes=60, worked_on="2026-10-28"):
    return client.post(
        "/time-entries",
        headers=headers,
        json={
            "task_id": task_id,
            "minutes": minutes,
            "worked_on": worked_on,
        },
    )


def create_owned_task(client, headers):
    client_id = create_client(client, headers, "Time Entry Test Client")
    project_id = create_project(client, headers, client_id, "Time Entry Test Project")
    task_response = create_task(client, headers, project_id, "Prepare report")
    assert task_response.status_code == 201, task_response.text
    return task_response.json()["id"]


def test_create_list_and_delete_time_entry(client):
    headers = register_and_login(client, "time-entry-crud@example.com")
    task_id = create_owned_task(client, headers)

    created = create_time_entry(client, headers, task_id, 75)
    assert created.status_code == 201, created.text

    entry = created.json()
    entry_id = entry["id"]
    assert entry["task_id"] == task_id
    assert entry["minutes"] == 75
    assert entry["worked_on"] == "2026-10-28"
    assert entry["billed"] is False
    assert "created_at" in entry

    listed = client.get(
        "/time-entries",
        headers=headers,
        params={"task_id": task_id},
    )
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == entry_id for item in listed.json())

    deleted = client.delete(f"/time-entries/{entry_id}", headers=headers)
    assert deleted.status_code == 204

    listed_again = client.get(
        "/time-entries",
        headers=headers,
        params={"task_id": task_id},
    )
    assert listed_again.status_code == 200
    assert all(item["id"] != entry_id for item in listed_again.json())


def test_time_entry_requires_authentication(client):
    response = client.post(
        "/time-entries",
        json={
            "task_id": 1,
            "minutes": 30,
            "worked_on": "2026-10-28",
        },
    )
    assert response.status_code == 401


def test_time_entry_rejects_zero_and_negative_minutes(client):
    headers = register_and_login(client, "time-entry-validation@example.com")
    task_id = create_owned_task(client, headers)

    for invalid_minutes in (0, -10):
        response = create_time_entry(
            client,
            headers,
            task_id,
            minutes=invalid_minutes,
        )
        assert response.status_code == 422, response.text


def test_cannot_create_time_entry_for_another_users_task(client):
    owner = register_and_login(client, "time-entry-owner@example.com")
    visitor = register_and_login(client, "time-entry-visitor@example.com")
    task_id = create_owned_task(client, owner)

    response = create_time_entry(client, visitor, task_id)
    assert response.status_code == 404


def test_cannot_list_time_entries_for_another_users_task(client):
    owner = register_and_login(client, "time-entry-list-owner@example.com")
    visitor = register_and_login(client, "time-entry-list-visitor@example.com")
    task_id = create_owned_task(client, owner)

    created = create_time_entry(client, owner, task_id)
    assert created.status_code == 201, created.text

    response = client.get(
        "/time-entries",
        headers=visitor,
        params={"task_id": task_id},
    )
    assert response.status_code == 404


def test_billed_time_entry_cannot_be_deleted(client):
    headers = register_and_login(client, "time-entry-billed@example.com")
    task_id = create_owned_task(client, headers)

    created = create_time_entry(client, headers, task_id)
    assert created.status_code == 201, created.text
    entry_id = created.json()["id"]

    # Simulate an entry that has already been billed.
    db = TestingSessionLocal()
    try:
        entry = db.get(__import__("app.models.time_entry", fromlist=["TimeEntry"]).TimeEntry, entry_id)
        assert entry is not None
        entry.billed = True
        db.commit()
    finally:
        db.close()

    deleted = client.delete(f"/time-entries/{entry_id}", headers=headers)
    assert deleted.status_code == 409

    # The billed entry must remain in the database.
    db = TestingSessionLocal()
    try:
        entry = db.get(__import__("app.models.time_entry", fromlist=["TimeEntry"]).TimeEntry, entry_id)
        assert entry is not None
        assert entry.billed is True
    finally:
        db.close()
