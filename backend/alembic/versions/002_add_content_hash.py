"""add content_hash to documents

Revision ID: 002
Revises: 001
Create Date: 2026-07-18
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"


def upgrade():
    # Idempotent: column may already exist from manual migration.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("documents")}
    if "content_hash" not in columns:
        op.add_column("documents", sa.Column("content_hash", sa.String(64), nullable=True))

    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}
    if "ix_documents_content_hash" not in indexes:
        op.create_index("ix_documents_content_hash", "documents", ["content_hash"])


def downgrade():
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "content_hash")
