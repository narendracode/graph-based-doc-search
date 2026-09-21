"""Exclusive, per-document access grants — independent of a document's own zone/project
tags. Three kinds, all additive to the normal zone/project access rule:

- DocumentShare: one specific user gets access to this one document.
- DocumentZoneShare: everyone who has access to a given zone gets access to this one
  document, even if the document itself belongs to a different zone/project. Dynamic —
  if someone is granted that zone later, they gain access to this document too.
- DocumentProjectShare: same, but keyed on project instead of zone.

None of these change the document's actual zone_id/project_id (its "home" tags for
organization/browsing) — they're additional access paths layered on top.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import UUIDPKMixin


class DocumentShare(UUIDPKMixin, Base):
    __tablename__ = "document_shares"
    __table_args__ = (
        UniqueConstraint("document_id", "user_id", name="uq_document_share_doc_user"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship()
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    granted_by_user: Mapped["User"] = relationship(foreign_keys=[granted_by])


class DocumentZoneShare(UUIDPKMixin, Base):
    __tablename__ = "document_zone_shares"
    __table_args__ = (
        UniqueConstraint("document_id", "zone_id", name="uq_document_zone_share"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), index=True
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship()
    zone: Mapped["Zone"] = relationship()
    granted_by_user: Mapped["User"] = relationship()


class DocumentProjectShare(UUIDPKMixin, Base):
    __tablename__ = "document_project_shares"
    __table_args__ = (
        UniqueConstraint("document_id", "project_id", name="uq_document_project_share"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship()
    project: Mapped["Project"] = relationship()
    granted_by_user: Mapped["User"] = relationship()
