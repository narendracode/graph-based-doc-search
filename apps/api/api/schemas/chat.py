import uuid
from datetime import datetime

from pydantic import BaseModel

from api.models.chat import MessageRole


class ChatMessageIn(BaseModel):
    content: str


class CitationOut(BaseModel):
    id: uuid.UUID
    filename: str
    url: str


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list[CitationOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    messages: list[ChatMessageOut] = []
