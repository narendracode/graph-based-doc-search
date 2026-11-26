"""One-off reset: wipes all uploaded/test content back to exactly the state
`make seed` produces, for a fresh NBCC test cycle.

Keeps: the super admin, the seeded "zone.northern" demo user, the Default
zone/project, and the 4 sample zones/projects seed.py creates. Deletes
everything else: every document (file + Neo4j graph + DB row, chunks/shares
cascade at the DB level), every checklist item (seed.py never creates any, so
all of them are test artifacts), every chat session, and any zone/project/user
created beyond the seeded baseline.

Run via: uv run python -m api.scripts.reset_demo_data
"""

from api.config import get_settings
from api.db import SessionLocal
from api.models.chat import ChatSession
from api.models.checklist import ChecklistItem
from api.models.document import Document
from api.models.user import User
from api.models.zone_project import Project, Zone
from api.services import graph, storage

BASELINE_ZONE_CODES = {"DEFAULT", "NZ", "SZ", "EZ", "WZ"}
BASELINE_PROJECT_CODES = {"DEFAULT", "DME", "CHB", "MCR", "BIP"}


def main() -> None:
    settings = get_settings()
    baseline_usernames = {settings.superadmin_username, "zone.northern"}

    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        for doc in documents:
            storage.delete_file(doc.storage_path)
            graph.delete_document(doc.id)
            db.delete(doc)
        db.flush()

        checklist_items = db.query(ChecklistItem).all()
        for item in checklist_items:
            db.delete(item)
        db.flush()

        chat_sessions = db.query(ChatSession).all()
        for session in chat_sessions:
            db.delete(session)
        db.flush()

        projects = db.query(Project).filter(~Project.code.in_(BASELINE_PROJECT_CODES)).all()
        for project in projects:
            db.delete(project)
        zones = db.query(Zone).filter(~Zone.code.in_(BASELINE_ZONE_CODES)).all()
        for zone in zones:
            db.delete(zone)
        db.flush()

        users = db.query(User).filter(~User.username.in_(baseline_usernames)).all()
        for user in users:
            db.delete(user)

        db.commit()
        print(
            f"Reset complete: removed {len(documents)} document(s), "
            f"{len(checklist_items)} checklist item(s), {len(chat_sessions)} chat session(s), "
            f"{len(projects)} project(s), {len(zones)} zone(s), {len(users)} user(s). "
            "Default + 4 sample zones/projects, the super admin, and zone.northern remain."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
