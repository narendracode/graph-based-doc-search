import uuid
from datetime import datetime

from pydantic import BaseModel


class ShareUserCreate(BaseModel):
    username: str


class ShareUserOut(BaseModel):
    user_id: uuid.UUID
    username: str
    granted_by: str | None
    created_at: datetime


class ShareZoneCreate(BaseModel):
    zone_id: uuid.UUID


class ShareZoneOut(BaseModel):
    zone_id: uuid.UUID
    zone_name: str
    granted_by: str | None
    created_at: datetime


class ShareProjectCreate(BaseModel):
    project_id: uuid.UUID


class ShareProjectOut(BaseModel):
    project_id: uuid.UUID
    project_name: str
    granted_by: str | None
    created_at: datetime


class DocumentSharesOut(BaseModel):
    users: list[ShareUserOut]
    zones: list[ShareZoneOut]
    projects: list[ShareProjectOut]


class DocumentRetag(BaseModel):
    zone_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
