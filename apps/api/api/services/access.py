"""Single source of truth for document access control.

A super_admin sees everything. Everyone else sees a document if any of these hold:
- its zone is one of their granted zones (or the default zone), or
- its project is one of their granted projects (or the default project), or
- the document has been directly shared with them (DocumentShare), or
- the document has been exclusively shared with a zone they have access to
  (DocumentZoneShare) — even if the document's own zone/project differs, or
- likewise for a project (DocumentProjectShare).

All five are independent grant mechanisms, not a combined AND requirement.
"""

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from api.models.document import Document
from api.models.sharing import DocumentProjectShare, DocumentShare, DocumentZoneShare
from api.models.user import User, UserProjectAccess, UserRole, UserZoneAccess
from api.models.zone_project import Project, Zone


def accessible_zone_ids(db: Session, user: User) -> set[uuid.UUID]:
    default_ids = {z.id for z in db.query(Zone.id).filter(Zone.is_default.is_(True))}
    granted = {
        row.zone_id
        for row in db.query(UserZoneAccess.zone_id).filter(UserZoneAccess.user_id == user.id)
    }
    return default_ids | granted


def accessible_project_ids(db: Session, user: User) -> set[uuid.UUID]:
    default_ids = {p.id for p in db.query(Project.id).filter(Project.is_default.is_(True))}
    granted = {
        row.project_id
        for row in db.query(UserProjectAccess.project_id).filter(
            UserProjectAccess.user_id == user.id
        )
    }
    return default_ids | granted


def apply_document_access_filter(query: Query, db: Session, user: User) -> Query:
    """Scope a Document query (or a query joined against Document) to what `user` may see."""
    if user.role == UserRole.super_admin:
        return query

    zone_ids = accessible_zone_ids(db, user)
    project_ids = accessible_project_ids(db, user)
    user_shared = db.query(DocumentShare.document_id).filter(DocumentShare.user_id == user.id)
    zone_shared = db.query(DocumentZoneShare.document_id).filter(
        DocumentZoneShare.zone_id.in_(zone_ids)
    )
    project_shared = db.query(DocumentProjectShare.document_id).filter(
        DocumentProjectShare.project_id.in_(project_ids)
    )
    return query.filter(
        or_(
            Document.zone_id.in_(zone_ids),
            Document.project_id.in_(project_ids),
            Document.id.in_(user_shared),
            Document.id.in_(zone_shared),
            Document.id.in_(project_shared),
        )
    )


def can_access_document(db: Session, user: User, document: Document) -> bool:
    if user.role == UserRole.super_admin:
        return True

    zone_ids = accessible_zone_ids(db, user)
    project_ids = accessible_project_ids(db, user)
    if document.zone_id in zone_ids or document.project_id in project_ids:
        return True

    if (
        db.query(DocumentShare)
        .filter(DocumentShare.document_id == document.id, DocumentShare.user_id == user.id)
        .first()
        is not None
    ):
        return True

    if (
        db.query(DocumentZoneShare)
        .filter(
            DocumentZoneShare.document_id == document.id,
            DocumentZoneShare.zone_id.in_(zone_ids),
        )
        .first()
        is not None
    ):
        return True

    return (
        db.query(DocumentProjectShare)
        .filter(
            DocumentProjectShare.document_id == document.id,
            DocumentProjectShare.project_id.in_(project_ids),
        )
        .first()
        is not None
    )
