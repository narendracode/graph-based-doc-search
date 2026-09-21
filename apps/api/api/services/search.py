"""Hybrid search: Postgres full-text (tsvector) + pgvector cosine similarity,
combined via Reciprocal Rank Fusion (RRF). Every result is scoped by the caller's
zone/project access.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models.document import Document, DocumentChunk
from api.models.user import User
from api.services.access import apply_document_access_filter
from api.services.ollama_client import embed

RRF_K = 60
CANDIDATE_LIMIT = 50
# pgvector's cosine_distance always returns *some* nearest neighbor, however poor the
# match — without a cutoff, a nonsense query still "matches" every document in the
# archive. Empirically (nomic-embed-text), genuinely relevant results score well
# under 0.4; unrelated ones land around 0.6+. 0.5 sits in the gap between them.
MAX_VECTOR_DISTANCE = 0.5


def _keyword_candidates(db: Session, query: str) -> list:
    tsquery = func.plainto_tsquery("english", query)
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.content,
            func.ts_rank_cd(DocumentChunk.content_tsv, tsquery).label("rank"),
        )
        .where(DocumentChunk.content_tsv.op("@@")(tsquery))
        .order_by(func.ts_rank_cd(DocumentChunk.content_tsv, tsquery).desc())
        .limit(CANDIDATE_LIMIT)
    )
    return db.execute(stmt).all()


def _vector_candidates(db: Session, query_embedding: list[float]) -> list:
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk.id, DocumentChunk.document_id, DocumentChunk.content, distance.label("distance"))
        .where(DocumentChunk.embedding.is_not(None), distance < MAX_VECTOR_DISTANCE)
        .order_by(distance.asc())
        .limit(CANDIDATE_LIMIT)
    )
    return db.execute(stmt).all()


def _ranked_documents(db: Session, user: User, query: str, limit: int) -> list[dict]:
    """RRF-combined, access-scoped documents with their best-matching chunk content
    (full, untruncated). Shared by search results and RAG chat context."""
    keyword_rows = _keyword_candidates(db, query)
    vector_rows = _vector_candidates(db, embed(query))

    rrf_scores: dict[uuid.UUID, float] = {}
    content_by_chunk: dict[uuid.UUID, tuple[uuid.UUID, str]] = {}
    for rank, row in enumerate(keyword_rows, start=1):
        rrf_scores[row.id] = rrf_scores.get(row.id, 0.0) + 1.0 / (RRF_K + rank)
        content_by_chunk[row.id] = (row.document_id, row.content)
    for rank, row in enumerate(vector_rows, start=1):
        rrf_scores[row.id] = rrf_scores.get(row.id, 0.0) + 1.0 / (RRF_K + rank)
        content_by_chunk[row.id] = (row.document_id, row.content)

    # Keep only the best-scoring chunk per document as that document's snippet/score.
    best_per_doc: dict[uuid.UUID, tuple[float, str]] = {}
    for chunk_id, score in rrf_scores.items():
        doc_id, content = content_by_chunk[chunk_id]
        if doc_id not in best_per_doc or score > best_per_doc[doc_id][0]:
            best_per_doc[doc_id] = (score, content)

    if not best_per_doc:
        return []

    query_stmt = apply_document_access_filter(
        db.query(Document).filter(Document.id.in_(best_per_doc.keys())), db, user
    )
    docs = query_stmt.all()
    results = []
    for doc in docs:
        score, content = best_per_doc[doc.id]
        results.append(
            {
                "id": doc.id,
                "filename": doc.filename,
                "doc_type_name": doc.doc_type.name,
                "content": content,
                "score": score,
                "url": f"/documents/{doc.id}",
                "uploaded_by": doc.uploader.username if doc.uploader else None,
                "created_at": doc.created_at,
                "last_uploaded_at": doc.last_uploaded_at,
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def hybrid_search(db: Session, user: User, query: str, limit: int = 20) -> list[dict]:
    results = _ranked_documents(db, user, query, limit)
    for r in results:
        r["snippet"] = r.pop("content")[:300]
    return results


def retrieve_context(db: Session, user: User, query: str, limit: int = 5) -> list[dict]:
    """Top matching documents with full chunk content, for grounding AI Mode answers."""
    return _ranked_documents(db, user, query, limit)


def autocomplete(db: Session, user: User, query: str, limit: int = 10) -> list[dict]:
    q = apply_document_access_filter(
        db.query(Document).filter(Document.filename.ilike(f"%{query}%")), db, user
    )
    docs = q.order_by(Document.created_at.desc()).limit(limit).all()
    return [{"id": d.id, "filename": d.filename, "url": f"/documents/{d.id}"} for d in docs]
