import uuid
from datetime import datetime

from pydantic import BaseModel

from api.models.document import DocType, DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type: DocType
    zone_id: uuid.UUID
    zone_name: str
    project_id: uuid.UUID
    project_name: str
    status: DocumentStatus
    status_detail: str | None
    uploaded_by: str | None
    created_at: datetime
    last_uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: uuid.UUID
    filename: str
    doc_type: DocType
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
    doc_type: DocType
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
