import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user, require_super_admin
from api.models.checklist import ChecklistItem
from api.models.document import Document
from api.models.document_type import DocumentType
from api.models.user import User
from api.models.zone_project import Project
from api.schemas.checklist import (
    ChecklistDocumentOut,
    ChecklistItemCreate,
    ChecklistItemOut,
    ChecklistItemStatusOut,
    ChecklistItemUpdate,
    ProjectChecklistOut,
)
from api.schemas.zone_project import ProjectCreate, ProjectOut, ProjectUpdate
from api.services import checklist

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_project_or_404(db: Session, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


def _get_checklist_item_or_404(db: Session, project_id: uuid.UUID, item_id: uuid.UUID) -> ChecklistItem:
    item = db.get(ChecklistItem, item_id)
    if item is None or item.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist item not found")
    return item


def _checklist_document_out(d: Document) -> dict:
    return {
        "id": d.id,
        "filename": d.filename,
        "status": d.status,
        "review_status": d.review_status,
        "review_feedback": d.review_feedback,
        "reviewed_by": d.reviewer.username if d.reviewer else None,
        "reviewed_at": d.reviewed_at,
        "uploaded_by": d.uploader.username if d.uploader else None,
        "created_at": d.created_at,
        "url": f"/documents/{d.id}",
    }


def _checklist_item_status_out(item: ChecklistItem) -> dict:
    docs = sorted(item.documents, key=lambda d: d.created_at, reverse=True)
    latest = docs[0] if docs else None
    return {
        "id": item.id,
        "document_type_id": item.document_type_id,
        "document_type_name": item.document_type.name,
        "description": item.description,
        "order_index": item.order_index,
        "item_status": checklist.item_status(item),
        "latest_document": _checklist_document_out(latest) if latest else None,
        "documents": [_checklist_document_out(d) for d in docs],
    }


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[Project]:
    return db.query(Project).order_by(Project.name).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), _: User = Depends(require_super_admin)
) -> Project:
    project = Project(name=payload.name, code=payload.code)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if payload.name is not None:
        project.name = payload.name
    if payload.code is not None:
        project.code = payload.code
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> None:
    project = _get_project_or_404(db, project_id)
    if project.is_default:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The default project can't be deleted")

    doc_count = db.query(Document).filter(Document.project_id == project_id).count()
    if doc_count > 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Can't delete this project — {doc_count} document(s) are still tagged to it. "
            "Retag or delete them first.",
        )

    # Checklist items cascade automatically; any documents linked to them are just
    # unlinked (ChecklistItem.documents -> SET NULL), never deleted.
    db.delete(project)
    db.commit()


def _checklist_item_out(item: ChecklistItem) -> dict:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "document_type_id": item.document_type_id,
        "document_type_name": item.document_type.name,
        "description": item.description,
        "order_index": item.order_index,
        "created_at": item.created_at,
    }


@router.get("/{project_id}/checklist-items", response_model=list[ChecklistItemOut])
def list_checklist_items(
    project_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[dict]:
    _get_project_or_404(db, project_id)
    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.project_id == project_id)
        .order_by(ChecklistItem.order_index, ChecklistItem.created_at)
        .all()
    )
    return [_checklist_item_out(item) for item in items]


@router.post(
    "/{project_id}/checklist-items",
    response_model=ChecklistItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_checklist_item(
    project_id: uuid.UUID,
    payload: ChecklistItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
) -> dict:
    _get_project_or_404(db, project_id)
    if db.get(DocumentType, payload.document_type_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document type not found")
    item = ChecklistItem(
        project_id=project_id,
        document_type_id=payload.document_type_id,
        description=payload.description,
        order_index=payload.order_index,
        created_by=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _checklist_item_out(item)


@router.patch("/{project_id}/checklist-items/{item_id}", response_model=ChecklistItemOut)
def update_checklist_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> dict:
    item = _get_checklist_item_or_404(db, project_id, item_id)
    if payload.document_type_id is not None:
        if db.get(DocumentType, payload.document_type_id) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document type not found")
        item.document_type_id = payload.document_type_id
    if payload.description is not None:
        item.description = payload.description
    if payload.order_index is not None:
        item.order_index = payload.order_index
    db.commit()
    db.refresh(item)
    return _checklist_item_out(item)


@router.delete("/{project_id}/checklist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> None:
    item = _get_checklist_item_or_404(db, project_id, item_id)
    db.delete(item)
    db.commit()


@router.get("/{project_id}/checklist", response_model=ProjectChecklistOut)
def get_project_checklist(
    project_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> dict:
    project = _get_project_or_404(db, project_id)
    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.project_id == project_id)
        .order_by(ChecklistItem.order_index, ChecklistItem.created_at)
        .all()
    )
    status_value, label, approved_count, total_items = checklist.project_status(items)
    return {
        "project_id": project.id,
        "project_name": project.name,
        "project_status": status_value,
        "project_status_label": label,
        "approved_count": approved_count,
        "total_items": total_items,
        "items": [_checklist_item_status_out(item) for item in items],
    }
