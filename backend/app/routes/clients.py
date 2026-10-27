from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.security import get_current_user_id

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(
    payload: ClientCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Client:
    client = Client(user_id=user_id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientResponse])
def list_clients(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Client]:
    return (
        db.query(Client)
        .filter(Client.user_id == user_id)
        .order_by(Client.id)
        .all()
    )


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Client:
    client = db.query(Client).filter(
        Client.id == client_id, Client.user_id == user_id
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Client:
    client = db.query(Client).filter(
        Client.id == client_id, Client.user_id == user_id
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("name", "not-supplied") is None:
        raise HTTPException(status_code=422, detail="Name cannot be null")
    if updates.get("hourly_rate_cents", "not-supplied") is None:
        raise HTTPException(status_code=422, detail="Hourly rate cannot be null")

    for field, value in updates.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    client = db.query(Client).filter(
        Client.id == client_id, Client.user_id == user_id
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
