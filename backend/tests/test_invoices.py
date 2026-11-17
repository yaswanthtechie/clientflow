from conftest import TestingSessionLocal
from app.models.time_entry import TimeEntry

from tests.test_tasks import (
    create_client,
    create_project,
    create_task,
    register_and_login,
)


def create_time_entry(client, headers, task_id, minutes=60):
    return client.post(
        "/time-entries",
        headers=headers,
        json={
            "task_id": task_id,
            "minutes": minutes,
            "worked_on": "2026-10-28",
        },
    )


def create_invoice_context(client, headers):
    client_id = create_client(client, headers, "Invoice Test Client")
    project_id = create_project(
        client, headers, client_id, "Invoice Test Project"
    )
    task_response = create_task(
        client, headers, project_id, "Prepare invoice report"
    )
    assert task_response.status_code == 201, task_response.text

    return client_id, task_response.json()["id"]


def test_create_invoice_calculates_total_and_bills_entries(client):
    headers = register_and_login(client, "invoice-create@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry_one = create_time_entry(client, headers, task_id, 60)
    entry_two = create_time_entry(client, headers, task_id, 30)

    assert entry_one.status_code == 201, entry_one.text
    assert entry_two.status_code == 201, entry_two.text

    entry_ids = [entry_one.json()["id"], entry_two.json()["id"]]

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": entry_ids,
        },
    )

    assert response.status_code == 201, response.text

    invoice = response.json()
    assert invoice["client_id"] == client_id
    assert invoice["total_cents"] == 7500
    assert invoice["status"] == "draft"
    assert "created_at" in invoice

    db = TestingSessionLocal()
    try:
        for entry_id in entry_ids:
            entry = db.get(TimeEntry, entry_id)
            assert entry is not None
            assert entry.billed is True
            assert entry.invoice_id == invoice["id"]
    finally:
        db.close()


def test_list_and_retrieve_invoices(client):
    headers = register_and_login(client, "invoice-list@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    listed = client.get("/invoices", headers=headers)
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == invoice_id for item in listed.json())

    filtered = client.get(
        "/invoices",
        headers=headers,
        params={"client_id": client_id},
    )
    assert filtered.status_code == 200, filtered.text
    assert any(item["id"] == invoice_id for item in filtered.json())

    retrieved = client.get(
        f"/invoices/{invoice_id}",
        headers=headers,
    )
    assert retrieved.status_code == 200, retrieved.text
    assert retrieved.json()["id"] == invoice_id


def test_update_invoice_status(client):
    headers = register_and_login(client, "invoice-status@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    for invoice_status in ("sent", "paid", "draft"):
        response = client.patch(
            f"/invoices/{invoice_id}/status",
            headers=headers,
            json={"status": invoice_status},
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == invoice_status


def test_delete_invoice_releases_time_entries(client):
    headers = register_and_login(client, "invoice-delete@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text
    entry_id = entry.json()["id"]

    created = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry_id],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    deleted = client.delete(
        f"/invoices/{invoice_id}",
        headers=headers,
    )
    assert deleted.status_code == 204

    db = TestingSessionLocal()
    try:
        time_entry = db.get(TimeEntry, entry_id)
        assert time_entry is not None
        assert time_entry.invoice_id is None
        assert time_entry.billed is False
    finally:
        db.close()

    retrieved = client.get(
        f"/invoices/{invoice_id}",
        headers=headers,
    )
    assert retrieved.status_code == 404


def test_invoice_requires_authentication(client):
    response = client.get("/invoices")
    assert response.status_code == 401


def test_cannot_access_another_users_invoice(client):
    owner = register_and_login(client, "invoice-owner@example.com")
    visitor = register_and_login(client, "invoice-visitor@example.com")

    client_id, task_id = create_invoice_context(client, owner)
    entry = create_time_entry(client, owner, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=owner,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    retrieved = client.get(
        f"/invoices/{invoice_id}",
        headers=visitor,
    )
    assert retrieved.status_code == 404

    deleted = client.delete(
        f"/invoices/{invoice_id}",
        headers=visitor,
    )
    assert deleted.status_code == 404

    listed = client.get("/invoices", headers=visitor)
    assert listed.status_code == 200
    assert all(item["id"] != invoice_id for item in listed.json())


def test_cannot_create_invoice_for_another_users_client(client):
    owner = register_and_login(client, "invoice-client-owner@example.com")
    visitor = register_and_login(client, "invoice-client-visitor@example.com")

    client_id, _ = create_invoice_context(client, owner)

    response = client.post(
        "/invoices",
        headers=visitor,
        json={
            "client_id": client_id,
            "time_entry_ids": [1],
        },
    )
    assert response.status_code == 404


def test_duplicate_time_entry_ids_are_rejected(client):
    headers = register_and_login(client, "invoice-duplicate@example.com")
    client_id, _ = create_invoice_context(client, headers)

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [1, 1],
        },
    )
    assert response.status_code == 422


def test_already_invoiced_time_entry_cannot_be_invoiced_again(client):
    headers = register_and_login(client, "invoice-repeat@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text
    entry_id = entry.json()["id"]

    payload = {
        "client_id": client_id,
        "time_entry_ids": [entry_id],
    }

    first = client.post("/invoices", headers=headers, json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/invoices", headers=headers, json=payload)
    assert second.status_code == 409, second.text


def test_invalid_invoice_status_is_rejected(client):
    headers = register_and_login(client, "invoice-invalid-status@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text

    response = client.patch(
        f"/invoices/{created.json()['id']}/status",
        headers=headers,
        json={"status": "cancelled"},
    )
    assert response.status_code == 422

def test_invoice_total_rounds_to_nearest_cent(client):
    headers = register_and_login(client, "invoice-rounding@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id, 50)
    assert entry.status_code == 201, entry.text

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["total_cents"] == 4167


def test_cannot_invoice_time_entry_from_another_client(client):
    headers = register_and_login(client, "invoice-other-client@example.com")
    client_id, _ = create_invoice_context(client, headers)

    other_client_id = create_client(client, headers, "Second Client")
    other_project_id = create_project(
        client, headers, other_client_id, "Second Project"
    )
    other_task = create_task(client, headers, other_project_id, "Other task")
    assert other_task.status_code == 201, other_task.text

    entry = create_time_entry(client, headers, other_task.json()["id"])
    assert entry.status_code == 201, entry.text

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert response.status_code == 404


def test_cannot_update_status_of_another_users_invoice(client):
    owner = register_and_login(client, "invoice-status-owner@example.com")
    visitor = register_and_login(client, "invoice-status-visitor@example.com")

    client_id, task_id = create_invoice_context(client, owner)
    entry = create_time_entry(client, owner, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=owner,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    response = client.patch(
        f"/invoices/{invoice_id}/status",
        headers=visitor,
        json={"status": "paid"},
    )
    assert response.status_code == 404

    still_draft = client.get(f"/invoices/{invoice_id}", headers=owner)
    assert still_draft.json()["status"] == "draft"


def test_paid_invoice_cannot_be_deleted(client):
    headers = register_and_login(client, "invoice-paid-delete@example.com")
    client_id, task_id = create_invoice_context(client, headers)

    entry = create_time_entry(client, headers, task_id)
    assert entry.status_code == 201, entry.text

    created = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert created.status_code == 201, created.text
    invoice_id = created.json()["id"]

    updated = client.patch(
        f"/invoices/{invoice_id}/status",
        headers=headers,
        json={"status": "paid"},
    )
    assert updated.status_code == 200, updated.text

    deleted = client.delete(
        f"/invoices/{invoice_id}",
        headers=headers,
    )
    assert deleted.status_code == 409

    retrieved = client.get(
        f"/invoices/{invoice_id}",
        headers=headers,
    )
    assert retrieved.status_code == 200
    assert retrieved.json()["status"] == "paid"
