"""Document types are an admin-extensible taxonomy, not a fixed enum — any user can
add a new one (e.g. "Environmental Clearance") on the spot if it doesn't exist yet,
and it immediately becomes available both for tagging any uploaded document and for
building a project's checklist. This replaces the old fixed `DocType` enum."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import TimestampMixin, UUIDPKMixin


class DocumentType(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "document_types"

    name: Mapped[str] = mapped_column(String(150), unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped["User"] = relationship()
