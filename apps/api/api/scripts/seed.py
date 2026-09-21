"""Idempotent seed: super admin (from env), default zone/project, and a few sample
zones/projects/users for the demo story. Run via `make seed`."""

from api.config import get_settings
from api.db import SessionLocal
from api.models.user import User, UserRole, UserZoneAccess, UserProjectAccess
from api.models.zone_project import Project, Zone
from api.security import hash_password

settings = get_settings()

SAMPLE_ZONES = [
    ("Northern Zone", "NZ"),
    ("Southern Zone", "SZ"),
    ("Eastern Zone", "EZ"),
    ("Western Zone", "WZ"),
]
SAMPLE_PROJECTS = [
    ("Delhi Metro Extension", "DME"),
    ("Chennai Housing Board", "CHB"),
    ("Mumbai Coastal Road", "MCR"),
    ("Bengaluru IT Park", "BIP"),
]


def get_or_create_default_zone(db) -> Zone:
    zone = db.query(Zone).filter(Zone.is_default.is_(True)).first()
    if zone is None:
        zone = Zone(name="Default Zone", code="DEFAULT", is_default=True)
        db.add(zone)
        db.flush()
    return zone


def get_or_create_default_project(db) -> Project:
    project = db.query(Project).filter(Project.is_default.is_(True)).first()
    if project is None:
        project = Project(name="Default Project", code="DEFAULT", is_default=True)
        db.add(project)
        db.flush()
    return project


def get_or_create_superadmin(db) -> User:
    user = db.query(User).filter(User.username == settings.superadmin_username).first()
    if user is None:
        user = User(
            username=settings.superadmin_username,
            password_hash=hash_password(settings.superadmin_password),
            role=UserRole.super_admin,
        )
        db.add(user)
        db.flush()
    return user


def seed_sample_data(db) -> None:
    zones = {}
    for name, code in SAMPLE_ZONES:
        zone = db.query(Zone).filter(Zone.code == code).first()
        if zone is None:
            zone = Zone(name=name, code=code)
            db.add(zone)
            db.flush()
        zones[code] = zone

    projects = {}
    for name, code in SAMPLE_PROJECTS:
        project = db.query(Project).filter(Project.code == code).first()
        if project is None:
            project = Project(name=name, code=code)
            db.add(project)
            db.flush()
        projects[code] = project

    demo_user = db.query(User).filter(User.username == "zone.northern").first()
    if demo_user is None:
        demo_user = User(username="zone.northern", password_hash=hash_password("demo1234"))
        db.add(demo_user)
        db.flush()
        db.add(UserZoneAccess(user_id=demo_user.id, zone_id=zones["NZ"].id))
        db.add(UserProjectAccess(user_id=demo_user.id, project_id=projects["DME"].id))


def main() -> None:
    db = SessionLocal()
    try:
        get_or_create_default_zone(db)
        get_or_create_default_project(db)
        get_or_create_superadmin(db)
        seed_sample_data(db)
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
