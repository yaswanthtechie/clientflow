from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceStatusUpdate,
)
from app.security import get_current_user_id

router = APIRouter(prefix="/invoices", tags=["invoices"])


def get_owned_client(client_id: int, user_id: int, db: Session) -> Client:
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_owned_invoice(
    invoice_id: int,
    user_id: int,
    db: Session,
) -> Invoice:
    invoice = (
        db.query(Invoice)
        .join(Client, Invoice.client_id == Client.id)
        .filter(Invoice.id == invoice_id, Client.user_id == user_id)
        .first()
    )
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


def get_owned_time_entries(
    entry_ids: list[int],
    client_id: int,
    user_id: int,
    db: Session,
) -> list[TimeEntry]:
    entries = (
        db.query(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .join(Client, Project.client_id == Client.id)
        .filter(
            TimeEntry.id.in_(entry_ids),
            Client.id == client_id,
            Client.user_id == user_id,
        )
        .all()
    )

    if len(entries) != len(entry_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more time entries not found for this client",
        )

    return entries


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    payload: InvoiceCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Invoice:
    client = get_owned_client(payload.client_id, user_id, db)

    entries = get_owned_time_entries(
        payload.time_entry_ids,
        client.id,
        user_id,
        db,
    )

    if any(entry.billed or entry.invoice_id is not None for entry in entries):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more time entries are already invoiced",
        )

    total_minutes = sum(entry.minutes for entry in entries)

    total_cents = (
        total_minutes * client.hourly_rate_cents + 30
    ) // 60

    invoice = Invoice(
        client_id=client.id,
        total_cents=total_cents,
        status="draft",
    )

    db.add(invoice)
    db.flush()

    for entry in entries:
        entry.invoice_id = invoice.id
        entry.billed = True

    db.commit()
    db.refresh(invoice)

    return invoice


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    client_id: int | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Invoice]:
    query = (
        db.query(Invoice)
        .join(Client, Invoice.client_id == Client.id)
        .filter(Client.user_id == user_id)
    )

    if client_id is not None:
        get_owned_client(client_id, user_id, db)
        query = query.filter(Invoice.client_id == client_id)

    return query.order_by(Invoice.id).all()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def retrieve_invoice(
    invoice_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Invoice:
    return get_owned_invoice(invoice_id, user_id, db)


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
def update_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Invoice:
    invoice = get_owned_invoice(invoice_id, user_id, db)

    invoice.status = payload.status

    db.commit()
    db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    invoice = get_owned_invoice(invoice_id, user_id, db)

    if invoice.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paid invoices cannot be deleted",
        )

    entries = db.query(TimeEntry).filter(
        TimeEntry.invoice_id == invoice.id
    ).all()

    for entry in entries:
        entry.invoice_id = None
        entry.billed = False

    db.delete(invoice)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
