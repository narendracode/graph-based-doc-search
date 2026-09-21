"""Per-project checklists of required documents. An admin defines the items a
project's paperwork must satisfy — each one is a required document type, picked
from the same admin-extensible `DocumentType` list used to tag any upload — and
users upload documents against a specific item; each upload is approved/rejected.
Item and project completion status are always derived at read time from the linked
documents (see api/services/checklist.py) — never stored, so there's nothing to
drift out of sync when a document is reuploaded, approved, rejected, or a checklist
item is added/removed.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import TimestampMixin, UUIDPKMixin


class ChecklistItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "checklist_items"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="RESTRICT")
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    project: Mapped["Project"] = relationship()
    document_type: Mapped["DocumentType"] = relationship()
    creator: Mapped["User"] = relationship()
    documents: Mapped[list["Document"]] = relationship(back_populates="checklist_item")
