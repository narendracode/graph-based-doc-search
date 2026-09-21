import uuid

from api.models.document import Document, DocType
from api.models.sharing import DocumentProjectShare, DocumentShare, DocumentZoneShare
from api.models.user import User, UserProjectAccess, UserRole, UserZoneAccess
from api.models.zone_project import Project, Zone
from api.services.access import (
    accessible_zone_ids,
    apply_document_access_filter,
    can_access_document,
)


def _make_zone(db, name: str, is_default: bool = False) -> Zone:
    zone = Zone(name=name, code=f"{name[:8]}-{uuid.uuid4().hex[:6]}", is_default=is_default)
    db.add(zone)
    db.flush()
    return zone


def _make_project(db, name: str, is_default: bool = False) -> Project:
    project = Project(name=name, code=f"{name[:8]}-{uuid.uuid4().hex[:6]}", is_default=is_default)
    db.add(project)
    db.flush()
    return project


def _make_user(db) -> User:
    user = User(username=f"user-{uuid.uuid4().hex[:8]}", password_hash="x", role=UserRole.user)
    db.add(user)
    db.flush()
    return user


def _make_document(db, zone: Zone, project: Project) -> Document:
    doc = Document(
        filename="test.pdf",
        storage_path="/tmp/test.pdf",
        doc_type=DocType.other,
        zone_id=zone.id,
        project_id=project.id,
        checksum=uuid.uuid4().hex,
    )
    db.add(doc)
    db.flush()
    return doc


def test_default_zone_and_project_always_accessible(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    other_zone = _make_zone(db, "Other Zone")
    other_project = _make_project(db, "Other Project")
    user = _make_user(db)

    doc_in_default = _make_document(db, default_zone, default_project)
    doc_elsewhere = _make_document(db, other_zone, other_project)

    assert can_access_document(db, user, doc_in_default) is True
    assert can_access_document(db, user, doc_elsewhere) is False

    visible_ids = {d.id for d in apply_document_access_filter(db.query(Document), db, user).all()}
    assert doc_in_default.id in visible_ids
    assert doc_elsewhere.id not in visible_ids


def test_granted_zone_access_unlocks_its_documents(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    other_project = _make_project(db, "Other Project")
    granted_zone = _make_zone(db, "Granted Zone")
    other_zone = _make_zone(db, "Other Zone")
    user = _make_user(db)
    db.add(UserZoneAccess(user_id=user.id, zone_id=granted_zone.id))
    db.flush()

    doc_in_granted_zone = _make_document(db, granted_zone, default_project)
    # Neither its zone nor its project is granted/default, so it must stay hidden.
    doc_in_other_zone = _make_document(db, other_zone, other_project)

    assert can_access_document(db, user, doc_in_granted_zone) is True
    assert can_access_document(db, user, doc_in_other_zone) is False
    assert granted_zone.id in accessible_zone_ids(db, user)
    assert other_zone.id not in accessible_zone_ids(db, user)
    assert default_zone.id in accessible_zone_ids(db, user)


def test_super_admin_sees_everything(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    other_zone = _make_zone(db, "Other Zone")
    other_project = _make_project(db, "Other Project")
    admin = User(username=f"admin-{uuid.uuid4().hex[:8]}", password_hash="x", role=UserRole.super_admin)
    db.add(admin)
    db.flush()

    doc = _make_document(db, other_zone, other_project)
    db.add(doc)
    db.flush()

    assert can_access_document(db, admin, doc) is True
    visible_ids = {d.id for d in apply_document_access_filter(db.query(Document), db, admin).all()}
    assert doc.id in visible_ids


def test_direct_user_share_unlocks_a_specific_document(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    other_zone = _make_zone(db, "Other Zone")
    other_project = _make_project(db, "Other Project")
    user = _make_user(db)
    doc = _make_document(db, other_zone, other_project)

    assert can_access_document(db, user, doc) is False
    db.add(DocumentShare(document_id=doc.id, user_id=user.id))
    db.flush()
    assert can_access_document(db, user, doc) is True

    visible_ids = {d.id for d in apply_document_access_filter(db.query(Document), db, user).all()}
    assert doc.id in visible_ids


def test_exclusive_zone_share_unlocks_document_tagged_elsewhere(db):
    """A document tagged to Zone A / Project A can be exclusively shared with anyone
    who has access to Zone B — even though they have no overlap with A at all."""
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    home_zone = _make_zone(db, "Home Zone")
    home_project = _make_project(db, "Home Project")
    shared_zone = _make_zone(db, "Shared Zone")
    doc = _make_document(db, home_zone, home_project)

    user = _make_user(db)
    db.add(UserZoneAccess(user_id=user.id, zone_id=shared_zone.id))
    db.flush()

    assert can_access_document(db, user, doc) is False
    db.add(DocumentZoneShare(document_id=doc.id, zone_id=shared_zone.id))
    db.flush()
    assert can_access_document(db, user, doc) is True


def test_exclusive_project_share_unlocks_document_tagged_elsewhere(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    home_zone = _make_zone(db, "Home Zone")
    home_project = _make_project(db, "Home Project")
    shared_project = _make_project(db, "Shared Project")
    doc = _make_document(db, home_zone, home_project)

    user = _make_user(db)
    db.add(UserProjectAccess(user_id=user.id, project_id=shared_project.id))
    db.flush()

    assert can_access_document(db, user, doc) is False
    db.add(DocumentProjectShare(document_id=doc.id, project_id=shared_project.id))
    db.flush()
    assert can_access_document(db, user, doc) is True


def test_revoking_a_share_removes_access_again(db):
    default_zone = _make_zone(db, "Default", is_default=True)
    default_project = _make_project(db, "Default", is_default=True)
    other_zone = _make_zone(db, "Other Zone")
    other_project = _make_project(db, "Other Project")
    user = _make_user(db)
    doc = _make_document(db, other_zone, other_project)

    share = DocumentShare(document_id=doc.id, user_id=user.id)
    db.add(share)
    db.flush()
    assert can_access_document(db, user, doc) is True

    db.delete(share)
    db.flush()
    assert can_access_document(db, user, doc) is False
