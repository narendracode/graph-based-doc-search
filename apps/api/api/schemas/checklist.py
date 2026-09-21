import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from api.models.document import DocumentStatus, ReviewStatus


class ChecklistItemCreate(BaseModel):
    document_type_id: uuid.UUID
    description: str | None = None
    order_index: int = 0


class ChecklistItemUpdate(BaseModel):
    document_type_id: uuid.UUID | None = None
    description: str | None = None
    order_index: int | None = None


class ChecklistItemOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    document_type_id: uuid.UUID
    document_type_name: str
    description: str | None
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChecklistDocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    review_status: ReviewStatus | None
    review_feedback: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    uploaded_by: str | None
    created_at: datetime
    url: str


class ChecklistItemStatusOut(BaseModel):
    id: uuid.UUID
    document_type_id: uuid.UUID
    document_type_name: str
    description: str | None
    order_index: int
    item_status: Literal["not_uploaded", "pending_review", "approved", "rejected"]
    latest_document: ChecklistDocumentOut | None
    documents: list[ChecklistDocumentOut]


class ProjectChecklistOut(BaseModel):
    project_id: uuid.UUID
    project_name: str
    project_status: Literal["no_checklist", "pending", "completed"]
    project_status_label: str
    approved_count: int
    total_items: int
    items: list[ChecklistItemStatusOut]


class DocumentReviewCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    feedback: str | None = None


class DocumentReviewOut(BaseModel):
    id: uuid.UUID
    review_status: ReviewStatus
    review_feedback: str | None
    reviewed_by: str | None
    reviewed_at: datetime

    model_config = {"from_attributes": True}
