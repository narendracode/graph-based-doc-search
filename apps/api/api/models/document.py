import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.config import get_settings
from api.db import Base
from api.models.base import TimestampMixin, UUIDPKMixin

settings = get_settings()


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    parsing = "parsing"
    embedding = "embedding"
    graph_building = "graph_building"
    completed = "completed"
    failed = "failed"


class ReviewStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class Document(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(500))
    storage_path: Mapped[str] = mapped_column(String(1000))
    doc_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="RESTRICT")
    )
    checksum: Mapped[str] = mapped_column(String(64), index=True)

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="RESTRICT")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT")
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.pending
    )
    status_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Distinct from updated_at (which also shifts as the ingestion pipeline moves the
    # document through statuses) — this only changes on an actual upload/reupload, so
    # it means what it says in the UI.
    last_uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Set only when this document was uploaded against a specific checklist item —
    # ordinary archive uploads leave all of these null and are entirely unaffected
    # by the review workflow. A checklist item can have several documents over time
    # (one per upload attempt); its status is derived from the most recent one.
    checklist_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checklist_items.id", ondelete="SET NULL"), nullable=True
    )
    review_status: Mapped[ReviewStatus | None] = mapped_column(
        Enum(ReviewStatus, name="review_status"), nullable=True
    )
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    zone: Mapped["Zone"] = relationship()
    project: Mapped["Project"] = relationship()
    doc_type: Mapped["DocumentType"] = relationship()
    uploader: Mapped["User"] = relationship(foreign_keys=[uploaded_by])
    reviewer: Mapped["User"] = relationship(foreign_keys=[reviewed_by])
    checklist_item: Mapped["ChecklistItem"] = relationship(
        back_populates="documents", foreign_keys=[checklist_item_id]
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(UUIDPKMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")
