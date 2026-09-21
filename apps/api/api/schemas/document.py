import uuid
from datetime import datetime

from pydantic import BaseModel

from api.models.document import DocumentStatus, ReviewStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type_id: uuid.UUID
    doc_type_name: str
    zone_id: uuid.UUID
    zone_name: str
    project_id: uuid.UUID
    project_name: str
    status: DocumentStatus
    status_detail: str | None
    uploaded_by: str | None
    created_at: datetime
    last_uploaded_at: datetime
    checklist_item_id: uuid.UUID | None = None
    review_status: ReviewStatus | None = None
    review_feedback: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type_name: str
    zone_name: str
    project_name: str
    status: DocumentStatus
    uploaded_by: str | None
    created_at: datetime
    last_uploaded_at: datetime
    url: str


class RelatedDocument(BaseModel):
    id: uuid.UUID
    filename: str
    url: str
    reason: str
    excerpt: str | None = None
    uploaded_by: str | None
    created_at: datetime
    last_uploaded_at: datetime


class SearchResultItem(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type_name: str
    snippet: str
    score: float
    url: str
    uploaded_by: str | None
    created_at: datetime
    last_uploaded_at: datetime


class AutocompleteItem(BaseModel):
    id: uuid.UUID
    filename: str
    url: str


class ChunkOut(BaseModel):
    id: uuid.UUID
    chunk_index: int
    content: str
    has_embedding: bool


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class DocumentGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
