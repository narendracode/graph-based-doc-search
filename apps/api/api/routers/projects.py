import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user, require_super_admin
from api.models.user import User
from api.models.zone_project import Project
from api.schemas.zone_project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[Project]:
    return db.query(Project).order_by(Project.name).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), _: User = Depends(require_super_admin)
) -> Project:
    project = Project(name=payload.name, code=payload.code)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if payload.name is not None:
        project.name = payload.name
    if payload.code is not None:
        project.code = payload.code
    db.commit()
    db.refresh(project)
    return project
