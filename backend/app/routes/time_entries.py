from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryCreate, TimeEntryResponse
from app.security import get_current_user_id

router = APIRouter(prefix="/time-entries", tags=["time entries"])


def get_owned_task(task_id: int, user_id: int, db: Session) -> Task:
    task = (
        db.query(Task)
        .join(Project, Task.project_id == Project.id)
        .join(Client, Project.client_id == Client.id)
        .filter(Task.id == task_id, Client.user_id == user_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def get_owned_time_entry(
    entry_id: int,
    user_id: int,
    db: Session,
) -> TimeEntry:
    entry = (
        db.query(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .join(Client, Project.client_id == Client.id)
        .filter(TimeEntry.id == entry_id, Client.user_id == user_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry


@router.post(
    "",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_time_entry(
    payload: TimeEntryCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> TimeEntry:
    get_owned_task(payload.task_id, user_id, db)

    entry = TimeEntry(
        task_id=payload.task_id,
        minutes=payload.minutes,
        worked_on=payload.worked_on,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=list[TimeEntryResponse])
def list_time_entries(
    task_id: int | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[TimeEntry]:
    query = (
        db.query(TimeEntry)
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .join(Client, Project.client_id == Client.id)
        .filter(Client.user_id == user_id)
    )

    if task_id is not None:
        get_owned_task(task_id, user_id, db)
        query = query.filter(TimeEntry.task_id == task_id)

    return query.order_by(TimeEntry.id).all()


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_entry(
    entry_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    entry = get_owned_time_entry(entry_id, user_id, db)

    if entry.billed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Billed time entries cannot be deleted",
        )

    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
