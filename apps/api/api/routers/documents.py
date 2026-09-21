import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.models.document import Document, DocType, DocumentChunk, DocumentStatus
from api.models.sharing import DocumentProjectShare, DocumentShare, DocumentZoneShare
from api.models.user import User, UserRole
from api.models.zone_project import Project, Zone
from api.schemas.document import (
    ChunkOut,
    DocumentGraph,
    DocumentListItem,
    DocumentOut,
    RelatedDocument,
)
from api.schemas.sharing import (
    DocumentRetag,
    DocumentSharesOut,
    ShareProjectCreate,
    ShareProjectOut,
    ShareUserCreate,
    ShareUserOut,
    ShareZoneCreate,
    ShareZoneOut,
)
from api.services.access import apply_document_access_filter, can_access_document
from api.services import graph
from api.services import relatedness
from api.services import storage
from api.services.queue import ingestion_queue

router = APIRouter(prefix="/documents", tags=["documents"])


def _default_zone(db: Session) -> Zone:
    return db.query(Zone).filter(Zone.is_default.is_(True)).one()


def _default_project(db: Session) -> Project:
    return db.query(Project).filter(Project.is_default.is_(True)).one()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocType = Form(...),
    zone_id: uuid.UUID | None = Form(default=None),
    project_id: uuid.UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    zone = db.get(Zone, zone_id) if zone_id else _default_zone(db)
    project = db.get(Project, project_id) if project_id else _default_project(db)
    if zone is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Zone not found")
    if project is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project not found")

    document = Document(
        filename=file.filename,
        storage_path="",
        doc_type=doc_type,
        zone_id=zone.id,
        project_id=project.id,
        uploaded_by=user.id,
        checksum="",
    )
    db.add(document)
    db.flush()  # assign document.id before writing the file

    data = await file.read()
    storage_path, checksum = storage.save_upload(document.id, file.filename, data)
    document.storage_path = storage_path
    document.checksum = checksum
    db.commit()
    db.refresh(document)

    ingestion_queue.enqueue("api.pipeline.ingest.process_document", str(document.id))
    return _document_out(document)


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    zone_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    doc_type: DocType | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    query = db.query(Document)
    query = apply_document_access_filter(query, db, user)
    if zone_id:
        query = query.filter(Document.zone_id == zone_id)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)

    docs = query.order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "zone_name": d.zone.name,
            "project_name": d.project.name,
            "status": d.status,
            "uploaded_by": d.uploader.username if d.uploader else None,
            "created_at": d.created_at,
            "last_uploaded_at": d.last_uploaded_at,
            "url": f"/documents/{d.id}",
        }
        for d in docs
    ]


def _get_document_or_404(db: Session, user: User, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None or not can_access_document(db, user, document):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document


def _document_out(d: Document) -> dict:
    return {
        "id": d.id,
        "filename": d.filename,
        "doc_type": d.doc_type,
        "zone_id": d.zone_id,
        "zone_name": d.zone.name,
        "project_id": d.project_id,
        "project_name": d.project.name,
        "status": d.status,
        "status_detail": d.status_detail,
        "uploaded_by": d.uploader.username if d.uploader else None,
        "created_at": d.created_at,
        "last_uploaded_at": d.last_uploaded_at,
    }


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    return _document_out(_get_document_or_404(db, user, document_id))


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document_tags(
    document_id: uuid.UUID,
    payload: DocumentRetag,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Corrects a document's zone/project after upload — e.g. the wrong one was picked
    at upload time. Anyone with current access can fix it (same bar as delete/reupload
    in this app); it doesn't touch any exclusive shares already granted on the doc."""
    document = _get_document_or_404(db, user, document_id)

    if payload.zone_id is not None:
        zone = db.get(Zone, payload.zone_id)
        if zone is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Zone not found")
        document.zone_id = zone.id
    if payload.project_id is not None:
        project = db.get(Project, payload.project_id)
        if project is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project not found")
        document.project_id = project.id

    db.commit()
    db.refresh(document)

    graph.retag_document(
        document.id, document.filename, document.zone_id, document.zone.name,
        document.project_id, document.project.name,
    )
    return _document_out(document)


@router.get("/{document_id}/status", response_model=DocumentOut)
def get_status(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    return _document_out(_get_document_or_404(db, user, document_id))


@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> FileResponse:
    document = _get_document_or_404(db, user, document_id)
    return FileResponse(document.storage_path, filename=document.filename)


@router.get("/{document_id}/related", response_model=list[RelatedDocument])
def get_related(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    _get_document_or_404(db, user, document_id)
    related = graph.related_documents(document_id)

    accessible = []
    docs_by_id: dict[str, Document] = {}
    for r in related:
        doc = db.get(Document, uuid.UUID(r["id"]))
        if doc is None or not can_access_document(db, user, doc):
            continue
        docs_by_id[r["id"]] = doc
        accessible.append(r)

    explained = relatedness.explain(db, accessible)
    return [
        {
            "id": docs_by_id[r["id"]].id,
            "filename": docs_by_id[r["id"]].filename,
            "url": f"/documents/{docs_by_id[r['id']].id}",
            "reason": r["reason"],
            "excerpt": r["excerpt"],
            "uploaded_by": docs_by_id[r["id"]].uploader.username if docs_by_id[r["id"]].uploader else None,
            "created_at": docs_by_id[r["id"]].created_at,
            "last_uploaded_at": docs_by_id[r["id"]].last_uploaded_at,
        }
        for r in explained
    ]


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def get_chunks(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    _get_document_or_404(db, user, document_id)
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    return [
        {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "has_embedding": c.embedding is not None,
        }
        for c in chunks
    ]


@router.get("/{document_id}/graph", response_model=DocumentGraph)
def get_document_graph(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    _get_document_or_404(db, user, document_id)
    return graph.document_graph(document_id)


@router.get("/{document_id}/shares", response_model=DocumentSharesOut)
def list_shares(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    _get_document_or_404(db, user, document_id)
    user_shares = db.query(DocumentShare).filter(DocumentShare.document_id == document_id).all()
    zone_shares = (
        db.query(DocumentZoneShare).filter(DocumentZoneShare.document_id == document_id).all()
    )
    project_shares = (
        db.query(DocumentProjectShare).filter(DocumentProjectShare.document_id == document_id).all()
    )
    return {
        "users": [
            {
                "user_id": s.user_id,
                "username": s.user.username,
                "granted_by": s.granted_by_user.username if s.granted_by_user else None,
                "created_at": s.created_at,
            }
            for s in user_shares
        ],
        "zones": [
            {
                "zone_id": s.zone_id,
                "zone_name": s.zone.name,
                "granted_by": s.granted_by_user.username if s.granted_by_user else None,
                "created_at": s.created_at,
            }
            for s in zone_shares
        ],
        "projects": [
            {
                "project_id": s.project_id,
                "project_name": s.project.name,
                "granted_by": s.granted_by_user.username if s.granted_by_user else None,
                "created_at": s.created_at,
            }
            for s in project_shares
        ],
    }


@router.post(
    "/{document_id}/shares/users", response_model=ShareUserOut, status_code=status.HTTP_201_CREATED
)
def create_user_share(
    document_id: uuid.UUID,
    payload: ShareUserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    # Anyone who can already see the document can loop someone else in — matching
    # how sharing works in most document tools: view access is enough to share.
    _get_document_or_404(db, user, document_id)

    target = db.query(User).filter(User.username == payload.username).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user found with that username")
    if target.role == UserRole.super_admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Super admins already have access to everything")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You already have access to this document")

    existing = (
        db.query(DocumentShare)
        .filter(DocumentShare.document_id == document_id, DocumentShare.user_id == target.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already shared with this user")

    share = DocumentShare(document_id=document_id, user_id=target.id, granted_by=user.id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return {
        "user_id": target.id,
        "username": target.username,
        "granted_by": user.username,
        "created_at": share.created_at,
    }


@router.delete("/{document_id}/shares/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_share(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    _get_document_or_404(db, user, document_id)
    share = (
        db.query(DocumentShare)
        .filter(DocumentShare.document_id == document_id, DocumentShare.user_id == user_id)
        .first()
    )
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
    if user.role != UserRole.super_admin and share.granted_by != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only the person who shared this, or an admin, can revoke it"
        )
    db.delete(share)
    db.commit()


@router.post(
    "/{document_id}/shares/zones", response_model=ShareZoneOut, status_code=status.HTTP_201_CREATED
)
def create_zone_share(
    document_id: uuid.UUID,
    payload: ShareZoneCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Grants access to everyone who has (or later gets) access to this zone —
    exclusive access independent of the document's own zone/project tags."""
    _get_document_or_404(db, user, document_id)

    zone = db.get(Zone, payload.zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    existing = (
        db.query(DocumentZoneShare)
        .filter(DocumentZoneShare.document_id == document_id, DocumentZoneShare.zone_id == zone.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already shared with this zone")

    share = DocumentZoneShare(document_id=document_id, zone_id=zone.id, granted_by=user.id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return {
        "zone_id": zone.id,
        "zone_name": zone.name,
        "granted_by": user.username,
        "created_at": share.created_at,
    }


@router.delete("/{document_id}/shares/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone_share(
    document_id: uuid.UUID,
    zone_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    _get_document_or_404(db, user, document_id)
    share = (
        db.query(DocumentZoneShare)
        .filter(DocumentZoneShare.document_id == document_id, DocumentZoneShare.zone_id == zone_id)
        .first()
    )
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
    if user.role != UserRole.super_admin and share.granted_by != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only the person who shared this, or an admin, can revoke it"
        )
    db.delete(share)
    db.commit()


@router.post(
    "/{document_id}/shares/projects",
    response_model=ShareProjectOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project_share(
    document_id: uuid.UUID,
    payload: ShareProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Grants access to everyone who has (or later gets) access to this project —
    exclusive access independent of the document's own zone/project tags."""
    _get_document_or_404(db, user, document_id)

    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    existing = (
        db.query(DocumentProjectShare)
        .filter(
            DocumentProjectShare.document_id == document_id,
            DocumentProjectShare.project_id == project.id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already shared with this project")

    share = DocumentProjectShare(document_id=document_id, project_id=project.id, granted_by=user.id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return {
        "project_id": project.id,
        "project_name": project.name,
        "granted_by": user.username,
        "created_at": share.created_at,
    }


@router.delete("/{document_id}/shares/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_share(
    document_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    _get_document_or_404(db, user, document_id)
    share = (
        db.query(DocumentProjectShare)
        .filter(
            DocumentProjectShare.document_id == document_id,
            DocumentProjectShare.project_id == project_id,
        )
        .first()
    )
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
    if user.role != UserRole.super_admin and share.granted_by != user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only the person who shared this, or an admin, can revoke it"
        )
    db.delete(share)
    db.commit()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    document = _get_document_or_404(db, user, document_id)
    storage.delete_file(document.storage_path)
    graph.delete_document(document.id)
    db.delete(document)  # cascades to document_chunks
    db.commit()


@router.post("/{document_id}/reupload", response_model=DocumentOut)
async def reupload_document(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    document = _get_document_or_404(db, user, document_id)

    storage.delete_file(document.storage_path)
    graph.delete_document(document.id)  # chunks are wiped by the ingestion job itself

    data = await file.read()
    storage_path, checksum = storage.save_upload(document.id, file.filename, data)
    document.filename = file.filename
    document.storage_path = storage_path
    document.checksum = checksum
    document.status = DocumentStatus.pending
    document.status_detail = None
    document.uploaded_by = user.id
    document.last_uploaded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(document)

    ingestion_queue.enqueue("api.pipeline.ingest.process_document", str(document.id))
    return _document_out(document)
