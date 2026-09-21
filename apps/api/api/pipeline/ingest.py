"""RQ job body: turns an uploaded PDF into searchable chunks + graph entries.

pending -> parsing -> embedding -> graph_building -> completed (or failed)
"""

import logging
import uuid

from api.db import SessionLocal
from api.models.document import Document, DocumentChunk, DocumentStatus
from api.services import graph
from api.services.entity_extraction import extract_entities
from api.services.ollama_client import embed
from api.services.parsing import parse_and_chunk

logger = logging.getLogger(__name__)


def _set_status(db, document: Document, status: DocumentStatus, detail: str | None = None) -> None:
    document.status = status
    document.status_detail = detail
    db.commit()


def process_document(document_id: str) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None:
            return

        try:
            _set_status(db, document, DocumentStatus.parsing)
            chunk_texts = parse_and_chunk(document.storage_path)
            if not chunk_texts:
                _set_status(db, document, DocumentStatus.failed, "No extractable text found")
                return

            _set_status(db, document, DocumentStatus.embedding)
            # Clear any previous chunks (reupload path).
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
            for index, text in enumerate(chunk_texts):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=text,
                        embedding=embed(text),
                    )
                )
            db.commit()

            _set_status(db, document, DocumentStatus.graph_building)
            graph.upsert_document(
                document_id=document.id,
                filename=document.filename,
                zone_id=document.zone_id,
                zone_name=document.zone.name,
                project_id=document.project_id,
                project_name=document.project.name,
            )
            entities = extract_entities("\n".join(chunk_texts[:5]))
            graph.upsert_entities(document.id, entities)

            _set_status(db, document, DocumentStatus.completed)
        except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
            logger.exception("Ingestion failed for document %s", document_id)
            _set_status(db, document, DocumentStatus.failed, str(exc)[:500])
    finally:
        db.close()


def delete_document_data(document_id: uuid.UUID) -> None:
    graph.delete_document(document_id)
