from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.security import get_current_user_id

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_owned_project(project_id: int, user_id: int, db: Session) -> Project:
    project = (
        db.query(Project)
        .join(Client, Project.client_id == Client.id)
        .filter(Project.id == project_id, Client.user_id == user_id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


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


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Task:
    get_owned_project(payload.project_id, user_id, db)

    task = Task(project_id=payload.project_id, title=payload.title.strip())
    if not task.title:
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Task]:
    get_owned_project(project_id, user_id, db)
    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id)
        .all()
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Task:
    return get_owned_task(task_id, user_id, db)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Task:
    task = get_owned_task(task_id, user_id, db)
    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided")

    for field, value in updates.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )
        if field == "title":
            value = value.strip()
            if not value:
                raise HTTPException(status_code=422, detail="Title cannot be empty")
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    task = get_owned_task(task_id, user_id, db)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
