import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentTypeCreate(BaseModel):
    name: str


class DocumentTypeOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
