from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.security import get_current_user_id

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_client(
    client_id: int, user_id: int, db: Session
) -> Client:
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def get_owned_project(
    project_id: int, user_id: int, db: Session
) -> Project:
    project = (
        db.query(Project)
        .join(Client, Project.client_id == Client.id)
        .filter(Project.id == project_id, Client.user_id == user_id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    get_owned_client(payload.client_id, user_id, db)

    project = Project(client_id=payload.client_id, name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    client_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Project]:
    get_owned_client(client_id, user_id, db)

    return (
        db.query(Project)
        .filter(Project.client_id == client_id)
        .order_by(Project.id)
        .all()
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    return get_owned_project(project_id, user_id, db)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    project = get_owned_project(project_id, user_id, db)
    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is None:
        raise HTTPException(status_code=422, detail="Name cannot be null")
    if "status" in updates and updates["status"] is None:
        raise HTTPException(status_code=422, detail="Status cannot be null")

    for field, value in updates.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Response:
    project = get_owned_project(project_id, user_id, db)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
