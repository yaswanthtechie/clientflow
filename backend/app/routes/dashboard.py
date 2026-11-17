from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.security import get_current_user_id

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    today = date.today()
    month_start = today.replace(day=1)

    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)

    total_clients = (
        db.query(func.count(Client.id))
        .filter(Client.user_id == user_id)
        .scalar()
        or 0
    )

    active_projects = (
        db.query(func.count(Project.id))
        .join(Client, Project.client_id == Client.id)
        .filter(
            Client.user_id == user_id,
            Project.status == "active",
        )
        .scalar()
        or 0
    )

    total_minutes = (
        db.query(func.coalesce(func.sum(TimeEntry.minutes), 0))
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .join(Client, Project.client_id == Client.id)
        .filter(
            Client.user_id == user_id,
            TimeEntry.worked_on >= month_start,
            TimeEntry.worked_on < next_month_start,
        )
        .scalar()
    )

    unpaid_cents = (
        db.query(func.coalesce(func.sum(Invoice.total_cents), 0))
        .join(Client, Invoice.client_id == Client.id)
        .filter(
            Client.user_id == user_id,
            Invoice.status.in_(["draft", "sent"]),
        )
        .scalar()
    )

    paid_cents = (
        db.query(func.coalesce(func.sum(Invoice.total_cents), 0))
        .join(Client, Invoice.client_id == Client.id)
        .filter(
            Client.user_id == user_id,
            Invoice.status == "paid",
        )
        .scalar()
    )

    return {
        "total_clients": int(total_clients),
        "active_projects": int(active_projects),
        "billable_hours_this_month": round(int(total_minutes) / 60, 2),
        "invoice_totals": {
            "unpaid_cents": int(unpaid_cents),
            "paid_cents": int(paid_cents),
        },
    }
