from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.models.document_type import DocumentType
from api.models.user import User
from api.schemas.document_type import DocumentTypeCreate, DocumentTypeOut

router = APIRouter(prefix="/document-types", tags=["document-types"])


@router.get("", response_model=list[DocumentTypeOut])
def list_document_types(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[DocumentType]:
    return db.query(DocumentType).order_by(DocumentType.name).all()


@router.post("", response_model=DocumentTypeOut, status_code=status.HTTP_201_CREATED)
def create_document_type(
    payload: DocumentTypeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentType:
    # Any user can add a missing type on the spot — e.g. while building a project
    # checklist or tagging an upload — it then becomes available to everyone.
    name = payload.name.strip()
    if not name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Name is required")

    existing = db.query(DocumentType).filter(DocumentType.name.ilike(name)).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This document type already exists")

    doc_type = DocumentType(name=name, created_by=user.id)
    db.add(doc_type)
    db.commit()
    db.refresh(doc_type)
    return doc_type
