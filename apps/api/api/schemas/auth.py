import uuid

from pydantic import BaseModel

from api.models.user import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole

    model_config = {"from_attributes": True}
