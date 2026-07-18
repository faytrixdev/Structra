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
    op.add_column("documents", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])


def downgrade():
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "content_hash")
