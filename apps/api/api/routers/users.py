import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import require_super_admin
from api.models.user import User, UserProjectAccess, UserZoneAccess
from api.schemas.user import (
    AssignProjectsRequest,
    AssignZonesRequest,
    UserCreate,
    UserDetailOut,
    UserOut,
    UserUpdate,
)
from api.security import hash_password

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_super_admin)])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.username).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserDetailOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    db.delete(user)
    db.commit()


@router.put("/{user_id}/zones", response_model=UserDetailOut)
def assign_zones(
    user_id: uuid.UUID, payload: AssignZonesRequest, db: Session = Depends(get_db)
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    db.query(UserZoneAccess).filter(UserZoneAccess.user_id == user_id).delete()
    for zone_id in payload.zone_ids:
        db.add(UserZoneAccess(user_id=user_id, zone_id=zone_id))
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/projects", response_model=UserDetailOut)
def assign_projects(
    user_id: uuid.UUID, payload: AssignProjectsRequest, db: Session = Depends(get_db)
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    db.query(UserProjectAccess).filter(UserProjectAccess.user_id == user_id).delete()
    for project_id in payload.project_ids:
        db.add(UserProjectAccess(user_id=user_id, project_id=project_id))
    db.commit()
    db.refresh(user)
    return user
