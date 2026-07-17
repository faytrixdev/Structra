import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text, BigInteger, Enum as SAEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.domain.types import KnowledgeType, RelationType, EntityType, ConditionType, DocumentStatus, MemberRole


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(512))
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(SAEnum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")
    organization = relationship("Organization")


class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger)
    page_count = Column(Integer)
    status = Column(SAEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED)
    extra_data = Column("metadata", JSON, default=dict)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    knowledge_objects = relationship("KnowledgeObject", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    section = Column(String(255))
    position = Column(Integer, nullable=False)
    document = relationship("Document", back_populates="chunks")


class KnowledgeObject(Base):
    __tablename__ = "knowledge_objects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(KnowledgeType), nullable=False)
    title = Column(String(255))
    statement = Column(Text, nullable=False)
    original_text = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    version = Column(Integer, default=1)
    extra_data = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    document = relationship("Document", back_populates="knowledge_objects")
    entities = relationship("KnowledgeEntity", back_populates="knowledge", cascade="all, delete-orphan")
    conditions = relationship("KnowledgeCondition", back_populates="knowledge", cascade="all, delete-orphan")
    source_relations = relationship("KnowledgeRelation", foreign_keys="KnowledgeRelation.source_id", back_populates="source", cascade="all, delete-orphan")
    target_relations = relationship("KnowledgeRelation", foreign_keys="KnowledgeRelation.target_id", back_populates="target", cascade="all, delete-orphan")


class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_objects.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(SAEnum(EntityType), nullable=False)
    value = Column(String(255), nullable=False)
    role = Column(String(255))
    knowledge = relationship("KnowledgeObject", back_populates="entities")


class KnowledgeCondition(Base):
    __tablename__ = "knowledge_conditions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_objects.id", ondelete="CASCADE"), nullable=False)
    condition_type = Column(SAEnum(ConditionType), nullable=False)
    description = Column(Text, nullable=False)
    knowledge = relationship("KnowledgeObject", back_populates="conditions")


class KnowledgeRelation(Base):
    __tablename__ = "knowledge_relations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_objects.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_objects.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(SAEnum(RelationType), nullable=False)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source = relationship("KnowledgeObject", foreign_keys=[source_id], back_populates="source_relations")
    target = relationship("KnowledgeObject", foreign_keys=[target_id], back_populates="target_relations")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(255), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    details = Column("details", JSON, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PipelineLog(Base):
    __tablename__ = "pipeline_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    step = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    duration_ms = Column(Integer)
    tokens_used = Column(Integer)
    model = Column(String(255))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
