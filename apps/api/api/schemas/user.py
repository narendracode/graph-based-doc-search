import uuid

from pydantic import BaseModel

from api.models.user import UserRole
from api.schemas.zone_project import ProjectOut, ZoneOut


class UserCreate(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    password: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserDetailOut(UserOut):
    zones: list[ZoneOut] = []
    projects: list[ProjectOut] = []


class AssignZonesRequest(BaseModel):
    zone_ids: list[uuid.UUID]


class AssignProjectsRequest(BaseModel):
    project_ids: list[uuid.UUID]
