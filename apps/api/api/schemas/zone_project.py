import uuid

from pydantic import BaseModel


class ZoneCreate(BaseModel):
    name: str
    code: str


class ZoneUpdate(BaseModel):
    name: str | None = None
    code: str | None = None


class ZoneOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    is_default: bool

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    code: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    code: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    is_default: bool

    model_config = {"from_attributes": True}
