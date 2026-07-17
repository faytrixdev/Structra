"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001"
down_revision = None


def upgrade():
    from app.database import Base
    from app.domain.models import (
        Organization, User, OrganizationMember, Document,
        DocumentChunk, KnowledgeObject, KnowledgeEntity,
        KnowledgeCondition, KnowledgeRelation, AuditLog, PipelineLog
    )
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    op.drop_table("pipeline_logs")
    op.drop_table("audit_logs")
    op.drop_table("knowledge_relations")
    op.drop_table("knowledge_conditions")
    op.drop_table("knowledge_entities")
    op.drop_table("knowledge_objects")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("organization_members")
    op.drop_table("users")
    op.drop_table("organizations")
