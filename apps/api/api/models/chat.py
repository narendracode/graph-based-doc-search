import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import UUIDPKMixin


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatSession(UUIDPKMixin, Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(UUIDPKMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE")
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    cited_document_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
