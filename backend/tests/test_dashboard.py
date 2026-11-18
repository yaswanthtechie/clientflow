from datetime import date, datetime, timedelta, timezone

from tests.test_tasks import (
    create_client,
    create_project,
    create_task,
    register_and_login,
)


def create_dashboard_invoice(client, headers, client_id, task_id, minutes, status_value):
    entry = client.post(
        "/time-entries",
        headers=headers,
        json={
            "task_id": task_id,
            "minutes": minutes,
            "worked_on": datetime.now(timezone.utc).date().isoformat(),
        },
    )
    assert entry.status_code == 201, entry.text

    invoice = client.post(
        "/invoices",
        headers=headers,
        json={
            "client_id": client_id,
            "time_entry_ids": [entry.json()["id"]],
        },
    )
    assert invoice.status_code == 201, invoice.text

    if status_value != "draft":
        updated = client.patch(
            f"/invoices/{invoice.json()['id']}/status",
            headers=headers,
            json={"status": status_value},
        )
        assert updated.status_code == 200, updated.text

    return invoice.json()


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")
    assert response.status_code == 401


def test_dashboard_calculations_and_user_isolation(client):
    owner = register_and_login(client, "dashboard-owner@example.com")
    other_user = register_and_login(client, "dashboard-other@example.com")

    # Owner's client and projects.
    owner_client_id = create_client(client, owner, "Owner Client")
    active_project_id = create_project(
        client, owner, owner_client_id, "Active Project"
    )
    archived_project_id = create_project(
        client, owner, owner_client_id, "Archived Project"
    )

    archived = client.patch(
        f"/projects/{archived_project_id}",
        headers=owner,
        json={"status": "archived"},
    )
    assert archived.status_code == 200, archived.text

    owner_task = create_task(client, owner, active_project_id)
    assert owner_task.status_code == 201, owner_task.text
    owner_task_id = owner_task.json()["id"]

    # Current-month entries and invoices.
    create_dashboard_invoice(
        client, owner, owner_client_id, owner_task_id, 60, "draft"
    )
    create_dashboard_invoice(
        client, owner, owner_client_id, owner_task_id, 120, "sent"
    )
    create_dashboard_invoice(
        client, owner, owner_client_id, owner_task_id, 180, "paid"
    )

    # Previous-month time must not be included.
    today = datetime.now(timezone.utc).date()
    previous_month = today.replace(day=1) - timedelta(days=1)
    previous_entry = client.post(
        "/time-entries",
        headers=owner,
        json={
            "task_id": owner_task_id,
            "minutes": 600,
            "worked_on": previous_month.isoformat(),
        },
    )
    assert previous_entry.status_code == 201, previous_entry.text

    # Another user's client, project, time entry and paid invoice.
    other_client_id = create_client(client, other_user, "Other Client")
    other_project_id = create_project(
        client, other_user, other_client_id, "Other Project"
    )
    other_task = create_task(client, other_user, other_project_id)
    assert other_task.status_code == 201, other_task.text

    create_dashboard_invoice(
        client,
        other_user,
        other_client_id,
        other_task.json()["id"],
        240,
        "paid",
    )

    response = client.get("/dashboard", headers=owner)
    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total_clients"] == 1
    assert data["active_projects"] == 1
    assert data["total_hours_logged_this_month"] == 6.0
    assert data["invoice_totals"]["unpaid_cents"] == 15000
    assert data["invoice_totals"]["paid_cents"] == 15000

    assert isinstance(data["invoice_totals"]["unpaid_cents"], int)
    assert isinstance(data["invoice_totals"]["paid_cents"], int)


def test_dashboard_for_new_user_returns_zeros(client):
    headers = register_and_login(client, "dashboard-empty@example.com")

    response = client.get("/dashboard", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "total_clients": 0,
        "active_projects": 0,
        "total_hours_logged_this_month": 0.0,
        "invoice_totals": {"unpaid_cents": 0, "paid_cents": 0},
    }
