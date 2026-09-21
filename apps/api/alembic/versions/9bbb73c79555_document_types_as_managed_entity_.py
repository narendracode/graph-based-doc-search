"""document types as managed entity, checklist items reference document type

Revision ID: 9bbb73c79555
Revises: 616625350b28
Create Date: 2026-09-21 17:29:21.586606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9bbb73c79555'
down_revision: Union[str, None] = '616625350b28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The old `doc_type` enum's values, mapped to the display names document_types rows
# get on backfill — matches what api/scripts/seed.py now seeds on a fresh DB.
LEGACY_DOC_TYPE_NAMES = {
    "approval": "Approval",
    "contract": "Contract",
    "project_plan": "Project Plan",
    "invoice": "Invoice",
    "agreement": "Agreement",
    "other": "Other",
}

old_doc_type_enum = postgresql.ENUM(
    "approval", "contract", "project_plan", "invoice", "agreement", "other", name="doc_type"
)


def upgrade() -> None:
    document_types = op.create_table(
        'document_types',
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    bind = op.get_bind()
    import uuid as uuid_module

    # Seed the legacy enum values as rows so any existing `documents.doc_type` data
    # backfills onto a real DocumentType instead of being silently lost.
    legacy_ids = {}
    for value, name in LEGACY_DOC_TYPE_NAMES.items():
        new_id = uuid_module.uuid4()
        bind.execute(document_types.insert().values(id=new_id, name=name))
        legacy_ids[value] = new_id

    # --- documents.doc_type (enum) -> documents.doc_type_id (FK) ---
    op.add_column('documents', sa.Column('doc_type_id', sa.UUID(), nullable=True))
    for value, new_id in legacy_ids.items():
        bind.execute(
            sa.text("UPDATE documents SET doc_type_id = :new_id WHERE doc_type = :value"),
            {"new_id": str(new_id), "value": value},
        )
    op.alter_column('documents', 'doc_type_id', nullable=False)
    op.create_foreign_key(
        'fk_documents_doc_type_id_document_types',
        'documents', 'document_types', ['doc_type_id'], ['id'], ondelete='RESTRICT',
    )
    op.drop_column('documents', 'doc_type')
    old_doc_type_enum.drop(bind, checkfirst=True)

    # --- checklist_items.name (free text) -> checklist_items.document_type_id (FK) ---
    # Existing checklist item names don't map onto the legacy enum at all (they were
    # always arbitrary, e.g. "Environmental Clearance") — auto-create a DocumentType
    # per distinct existing name so no existing checklist item loses its identity.
    op.add_column('checklist_items', sa.Column('document_type_id', sa.UUID(), nullable=True))
    distinct_names = bind.execute(sa.text("SELECT DISTINCT name FROM checklist_items")).fetchall()
    for (name,) in distinct_names:
        existing = bind.execute(
            sa.text("SELECT id FROM document_types WHERE name = :name"), {"name": name}
        ).fetchone()
        type_id = existing[0] if existing else uuid_module.uuid4()
        if existing is None:
            bind.execute(document_types.insert().values(id=type_id, name=name))
        bind.execute(
            sa.text("UPDATE checklist_items SET document_type_id = :type_id WHERE name = :name"),
            {"type_id": str(type_id), "name": name},
        )
    op.alter_column('checklist_items', 'document_type_id', nullable=False)
    op.create_foreign_key(
        'fk_checklist_items_document_type_id_document_types',
        'checklist_items', 'document_types', ['document_type_id'], ['id'], ondelete='RESTRICT',
    )
    op.drop_column('checklist_items', 'name')


def downgrade() -> None:
    bind = op.get_bind()

    op.add_column('checklist_items', sa.Column('name', sa.VARCHAR(length=300), nullable=True))
    bind.execute(
        sa.text(
            "UPDATE checklist_items SET name = document_types.name "
            "FROM document_types WHERE checklist_items.document_type_id = document_types.id"
        )
    )
    op.alter_column('checklist_items', 'name', nullable=False)
    op.drop_constraint('fk_checklist_items_document_type_id_document_types', 'checklist_items', type_='foreignkey')
    op.drop_column('checklist_items', 'document_type_id')

    old_doc_type_enum.create(bind, checkfirst=True)
    op.add_column('documents', sa.Column('doc_type', old_doc_type_enum, nullable=True))
    for value, name in LEGACY_DOC_TYPE_NAMES.items():
        bind.execute(
            sa.text(
                "UPDATE documents SET doc_type = :value FROM document_types "
                "WHERE documents.doc_type_id = document_types.id AND document_types.name = :name"
            ),
            {"value": value, "name": name},
        )
    # Anything backed by a document type with no legacy counterpart (created after
    # this migration, or auto-created from an old checklist item name) has no
    # matching enum value — fall back to "other" rather than leaving it null.
    bind.execute(sa.text("UPDATE documents SET doc_type = 'other' WHERE doc_type IS NULL"))
    op.alter_column('documents', 'doc_type', nullable=False)
    op.drop_constraint('fk_documents_doc_type_id_document_types', 'documents', type_='foreignkey')
    op.drop_column('documents', 'doc_type_id')

    op.drop_table('document_types')
