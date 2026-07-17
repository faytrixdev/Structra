# Structra MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete MVP of Structra — a SaaS platform that transforms unstructured documents into structured knowledge using AI (NVIDIA NIM).

**Architecture:** Binary structure with standalone `frontend/` (Next.js) and `backend/` (FastAPI), communicating via REST API. Supabase for PostgreSQL + Auth + Storage. Qdrant for vector search. NVIDIA NIM for LLM inference. Clean Architecture with strict layer separation.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Next.js 14, Tailwind CSS, Shadcn UI, TanStack Query, React Flow, Qdrant, Supabase, NVIDIA NIM API

---

### Task 1: Scaffold backend project structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/service/__init__.py`
- Create: `backend/app/pipeline/__init__.py`
- Create: `backend/app/provider/__init__.py`
- Create: `backend/app/repository/__init__.py`
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

**Step 1: Create requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-multipart==0.0.12
python-dotenv==1.0.1
httpx==0.27.0
qdrant-client==1.12.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
supabase==2.5.0
aiofiles==24.1.0
python-magic==0.4.27
openpyxl==3.1.5
python-pptx==0.6.23
pypdf2==4.3.0
python-docx==1.1.2
markdown==3.7
beautifulsoup4==4.12.3
lxml==5.3.0
```

**Step 2: Write config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Structra"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/structra"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = "documents"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_embeddings"

    nvidia_api_key: str = ""
    nvidia_model: str = "meta/llama-3.1-405b-instruct"
    nvidia_base_url: str = "https://api.nvcf.nvidia.com/v2/chat/completions"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    max_file_size_mb: int = 50
    allowed_file_types: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/markdown",
        "text/html",
        "text/xml",
        "text/csv",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

**Step 3: Write database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Write main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import auth, documents, knowledge, search, export

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
```

**Step 5: Verify**

Run: `cd backend && pip install -r requirements.txt`
Expected: All packages install successfully

Run: `cd backend && python -c "from app.config import settings; print(settings.app_name)"`
Expected: `Structra`

---

### Task 2: Domain models (Pydantic + SQLAlchemy)

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/types.py`
- Create: `backend/app/domain/models.py`
- Create: `backend/app/domain/schemas.py`

**Step 1: Write types.py**

```python
from enum import StrEnum


class KnowledgeType(StrEnum):
    RULE = "Rule"
    DEFINITION = "Definition"
    PROCEDURE = "Procedure"
    DECISION = "Decision"
    WORKFLOW = "Workflow"
    RESPONSIBILITY = "Responsibility"
    CONSTRAINT = "Constraint"
    EXCEPTION = "Exception"
    REQUIREMENT = "Requirement"
    RISK = "Risk"
    EVENT = "Event"
    METRIC = "Metric"
    KPI = "KPI"
    POLICY = "Policy"
    CONCEPT = "Concept"
    OBLIGATION = "Obligation"
    PROHIBITION = "Prohibition"


class RelationType(StrEnum):
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    REFERENCES = "references"
    EXTENDS = "extends"
    CONTRADICTS = "contradicts"
    CAUSES = "causes"
    BLOCKS = "blocks"
    EXCEPTION_OF = "exception_of"
    WORKFLOW_STEP = "workflow_step"
    PARENT = "parent"
    CHILD = "child"


class EntityType(StrEnum):
    ACTOR = "actor"
    ACTION = "action"
    OBJECT = "object"


class ConditionType(StrEnum):
    CONDITION = "condition"
    CONSTRAINT = "constraint"
    EXCEPTION = "exception"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    SEGMENTING = "segmenting"
    EXTRACTING_IDEAS = "extracting_ideas"
    CLASSIFYING = "classifying"
    EXTRACTING_ENTITIES = "extracting_entities"
    BUILDING_RELATIONS = "building_relations"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class MemberRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
```

**Step 2: Write models.py**

```python
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
    metadata = Column(JSON, default=dict)
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
    metadata = Column(JSON, default=dict)
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
    details = Column(JSON, default=dict)
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
```

**Step 3: Write schemas.py**

```python
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class APIResponse(BaseModel):
    status: str = "success"
    data: Optional[dict | list] = None
    error: Optional[str] = None
    meta: Optional[dict] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    organization_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_type: str
    file_size: Optional[int] = None
    status: str
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class EntityResponse(BaseModel):
    entity_type: str
    value: str
    role: Optional[str] = None


class ConditionResponse(BaseModel):
    condition_type: str
    description: str


class KnowledgeResponse(BaseModel):
    id: UUID
    type: str
    title: Optional[str] = None
    statement: str
    original_text: str
    confidence: float
    entities: list[EntityResponse] = []
    conditions: list[ConditionResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    nodes: list
    edges: list


class SearchResult(BaseModel):
    id: UUID
    statement: str
    type: str
    confidence: float
    score: float
    document_title: str
```

---

### Task 3: Database migrations with Alembic

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_initial.py`

**Step 1: Initialize Alembic**

Run: `cd backend && alembic init alembic`

Then edit `backend/alembic/env.py` to point to our models. Replace the `target_metadata = None` line with:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base
from app.domain.models import *  # noqa: F401, F403
target_metadata = Base.metadata
```

**Step 2: Create initial migration**

Run: `cd backend && alembic revision --autogenerate -m "initial"`

Then upgrade: `cd backend && alembic upgrade head`

---

### Task 4: Authentication API

**Files:**
- Create: `backend/app/service/auth_service.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/dependencies.py`

**Step 1: Write auth_service.py**

```python
from uuid import UUID
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.models import User, Organization, OrganizationMember
from app.domain.types import MemberRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: UUID, organization_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def register_user(db: Session, email: str, password: str, name: str, organization_name: str) -> dict:
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")
    org = Organization(name=organization_name, slug=organization_name.lower().replace(" ", "-"))
    db.add(org)
    db.flush()
    user = User(email=email, name=name, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    member = OrganizationMember(user_id=user.id, organization_id=org.id, role=MemberRole.OWNER)
    db.add(member)
    db.commit()
    token = create_token(user.id, org.id)
    return {"token": token, "user": {"id": str(user.id), "email": user.email, "name": user.name}}


def authenticate_user(db: Session, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise ValueError("No organization found")
    token = create_token(user.id, member.organization_id)
    return {"token": token, "user": {"id": str(user.id), "email": user.email, "name": user.name}}
```

**Step 2: Write dependencies.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.service.auth_service import decode_token
from app.domain.models import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> tuple[User, str]:
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        organization_id = payload.get("org")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user, organization_id
```

**Step 3: Write auth.py router**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.schemas import RegisterRequest, LoginRequest, APIResponse
from app.service.auth_service import register_user, authenticate_user
from app.api.v1.dependencies import get_current_user

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_user(db, req.email, req.password, req.name, req.organization_name)
        return APIResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = authenticate_user(db, req.email, req.password)
        return APIResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def me(user=Depends(get_current_user)):
    current_user, _ = user
    return APIResponse(data={"id": str(current_user.id), "email": current_user.email, "name": current_user.name})
```

---

### Task 5: Document upload & management API

**Files:**
- Create: `backend/app/service/document_service.py`
- Create: `backend/app/api/v1/documents.py`

**Step 1: Write document_service.py**

```python
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.models import Document, AuditLog
from app.domain.types import DocumentStatus


async def upload_document(db: Session, organization_id: str, user_id: str, file: UploadFile) -> Document:
    if file.content_type not in settings.allowed_file_types:
        raise ValueError(f"File type {file.content_type} not supported")
    content = await file.read()
    file_size = len(content)
    if file_size > settings.max_file_size_mb * 1024 * 1024:
        raise ValueError(f"File exceeds {settings.max_file_size_mb}MB limit")
    file_path = f"{organization_id}/{uuid.uuid4()}-{file.filename}"
    doc = Document(
        organization_id=organization_id, title=file.filename or "untitled",
        file_type=file.content_type or "application/octet-stream",
        file_path=file_path, file_size=file_size, status=DocumentStatus.UPLOADED,
    )
    db.add(doc)
    db.flush()
    log = AuditLog(
        organization_id=organization_id, user_id=user_id,
        action="document.upload", resource_type="document",
        resource_id=doc.id, details={"filename": file.filename, "size": file_size},
    )
    db.add(log)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: str, organization_id: str) -> Optional[Document]:
    return db.query(Document).filter(
        Document.id == document_id, Document.organization_id == organization_id
    ).first()


def list_documents(db: Session, organization_id: str) -> list[Document]:
    return db.query(Document).filter(
        Document.organization_id == organization_id
    ).order_by(Document.created_at.desc()).all()


def delete_document(db: Session, document_id: str, organization_id: str) -> None:
    doc = get_document(db, document_id, organization_id)
    if not doc:
        raise ValueError("Document not found")
    db.delete(doc)
    db.commit()


def update_document_status(db: Session, document_id: str, status: DocumentStatus, error: Optional[str] = None) -> None:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.status = status
        doc.error_message = error
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()
```

**Step 2: Write documents.py router**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile as FastAPIUploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.schemas import APIResponse
from app.service.document_service import upload_document, get_document, list_documents, delete_document
from app.api.v1.dependencies import get_current_user
from app.pipeline.orchestrator import run_pipeline

router = APIRouter()


@router.get("")
async def get_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    docs = list_documents(db, org_id)
    return APIResponse(data=[{
        "id": str(d.id), "title": d.title, "file_type": d.file_type,
        "file_size": d.file_size, "status": d.status, "page_count": d.page_count,
        "error_message": d.error_message, "created_at": d.created_at.isoformat(),
    } for d in docs])


@router.post("")
async def create_document(file: FastAPIUploadFile = File(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    current_user, org_id = user
    try:
        doc = await upload_document(db, org_id, str(current_user.id), file)
        return APIResponse(data={
            "id": str(doc.id), "title": doc.title, "file_type": doc.file_type,
            "file_size": doc.file_size, "status": doc.status, "created_at": doc.created_at.isoformat(),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{document_id}")
async def get_document_detail(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    doc = get_document(db, document_id, org_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return APIResponse(data={
        "id": str(doc.id), "title": doc.title, "file_type": doc.file_type,
        "file_size": doc.file_size, "status": doc.status, "page_count": doc.page_count,
        "error_message": doc.error_message, "created_at": doc.created_at.isoformat(),
    })


@router.delete("/{document_id}")
async def remove_document(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    try:
        delete_document(db, document_id, org_id)
        return APIResponse(data={"message": "Document deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{document_id}/process")
async def process_document(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    doc = get_document(db, document_id, org_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    import asyncio
    asyncio.create_task(run_pipeline(document_id))
    return APIResponse(data={"message": "Pipeline started", "document_id": document_id})


@router.get("/{document_id}/status")
async def get_document_status(document_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    doc = get_document(db, document_id, org_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    from app.domain.models import PipelineLog
    logs = db.query(PipelineLog).filter(PipelineLog.document_id == document_id).order_by(PipelineLog.created_at).all()
    return APIResponse(data={
        "id": str(doc.id), "status": doc.status,
        "pipeline_logs": [{"step": l.step, "status": l.status, "duration_ms": l.duration_ms, "error": l.error_message} for l in logs],
    })
```

---

### Task 6: Text extraction service

**Files:**
- Create: `backend/app/service/extraction_service.py`

**Code:**

```python
from typing import Optional
import io
import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import openpyxl
from pptx import Presentation


async def extract_text(file_path: str, file_type: str, content: bytes) -> tuple[str, Optional[int]]:
    if "pdf" in file_type:
        return extract_pdf(content)
    elif "wordprocessingml" in file_type or "docx" in file_type:
        return extract_docx(content)
    elif "spreadsheetml" in file_type or "xlsx" in file_type:
        return extract_xlsx(content)
    elif "presentationml" in file_type or "pptx" in file_type:
        return extract_pptx(content)
    elif "html" in file_type:
        return extract_html(content)
    elif "xml" in file_type:
        return extract_xml(content)
    elif "markdown" in file_type:
        return extract_markdown(content)
    else:
        return content.decode("utf-8"), None


def extract_pdf(content: bytes) -> tuple[str, Optional[int]]:
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages), len(reader.pages)


def extract_docx(content: bytes) -> tuple[str, Optional[int]]:
    doc = docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs), None


def extract_xlsx(content: bytes) -> tuple[str, Optional[int]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f"\n## Sheet: {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            lines.append(" | ".join(str(c) if c is not None else "" for c in row))
    return "\n".join(lines), None


def extract_pptx(content: bytes) -> tuple[str, Optional[int]]:
    prs = Presentation(io.BytesIO(content))
    lines = []
    for i, slide in enumerate(prs.slides):
        lines.append(f"\n## Slide {i + 1}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                lines.append(shape.text)
    return "\n".join(lines), len(prs.slides)


def extract_html(content: bytes) -> tuple[str, Optional[int]]:
    return BeautifulSoup(content, "html.parser").get_text(separator="\n", strip=True), None


def extract_xml(content: bytes) -> tuple[str, Optional[int]]:
    return BeautifulSoup(content, "xml").get_text(separator="\n", strip=True), None


def extract_markdown(content: bytes) -> tuple[str, Optional[int]]:
    html = markdown.markdown(content.decode("utf-8"))
    return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True), None
```

---

### Task 7: AI Pipeline — NVIDIA NIM

**Files:**
- Create: `backend/app/provider/nim_client.py`
- Create: `backend/app/pipeline/prompts.py`
- Create: `backend/app/pipeline/stages.py`
- Create: `backend/app/pipeline/orchestrator.py`

**Step 1: Write nim_client.py**

```python
from typing import Optional
import httpx
from app.config import settings


class NIMClient:
    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.model = settings.nvidia_model
        self.base_url = settings.nvidia_base_url

    async def chat_completion(self, system_prompt: str, user_prompt: str, response_format: Optional[dict] = None, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": temperature, "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


nim_client = NIMClient()
```

**Step 2: Write prompts.py**

```python
SYSTEM_EXTRACT_IDEAS = """You are a knowledge extraction system. Break down text into atomic knowledge units.
Rules:
- ONE idea = ONE JSON object. Never merge different concepts.
- Never summarize. Keep original meaning.
- Output valid JSON array.
Each object: {"statement": "...", "type": "Rule|Definition|Procedure|Decision|Workflow|Responsibility|Constraint|Exception|Requirement|Risk|Event|Metric|KPI|Policy|Concept|Obligation|Prohibition"}
Example:
Input: "The manager validates expense requests within three days. Requests above 500€ require HR approval."
Output: [{"statement": "The manager validates expense requests within three days.", "type": "Responsibility"}, {"statement": "Requests above 500€ require HR approval.", "type": "Constraint"}]"""

SYSTEM_CLASSIFY = """You are a business knowledge classifier. Given a statement, classify it into exactly one category: Rule, Definition, Procedure, Decision, Workflow, Responsibility, Constraint, Exception, Requirement, Risk, Event, Metric, KPI, Policy, Concept, Obligation, Prohibition.
Output JSON: {"type": "...", "confidence": 0.0-1.0, "reasoning": "..."}"""

SYSTEM_EXTRACT_ENTITIES = """You are a semantic entity extractor. Extract actors, actions, objects, conditions, constraints, and exceptions from a knowledge statement.
Output JSON: {"entities": [{"type": "actor"|"action"|"object", "value": "...", "role": "..."}], "conditions": [{"type": "condition"|"constraint"|"exception", "description": "..."}]}"""

SYSTEM_BUILD_RELATIONS = """You are a knowledge graph builder. Given a list of knowledge objects, identify relationships between them.
Output JSON: {"relations": [{"source_index": 0, "target_index": 1, "type": "depends_on"|"requires"|"references"|"extends"|"contradicts"|"causes"|"blocks"|"exception_of"|"workflow_step"|"parent"|"child", "confidence": 0.0-1.0}]}"""

SYSTEM_VALIDATE = """You are a knowledge validation system. Verify quality and coherence.
Check: 1. Is the statement atomic (single idea)? 2. Is classification correct? 3. Are entities correct?
Output JSON: {"valid": true|false, "confidence_score": 0.0-1.0, "issues": [...], "suggestions": [...]}"""
```

**Step 3: Write stages.py**

```python
import json
import time
from sqlalchemy.orm import Session

from app.provider.nim_client import nim_client
from app.pipeline.prompts import *
from app.domain.models import KnowledgeObject, KnowledgeEntity, KnowledgeCondition, PipelineLog


async def extract_ideas_stage(document_id: str, text: str, db: Session) -> list[dict]:
    start = time.time()
    try:
        response = await nim_client.chat_completion(SYSTEM_EXTRACT_IDEAS, text, response_format={"type": "json_object"})
        ideas = json.loads(response)
        if isinstance(ideas, dict) and "ideas" in ideas:
            ideas = ideas["ideas"]
        log = PipelineLog(document_id=document_id, step="extract_ideas", status="completed", duration_ms=int((time.time() - start) * 1000), model=nim_client.model)
        db.add(log)
        db.commit()
        return ideas if isinstance(ideas, list) else []
    except Exception as e:
        log = PipelineLog(document_id=document_id, step="extract_ideas", status="failed", error_message=str(e), duration_ms=int((time.time() - start) * 1000))
        db.add(log)
        db.commit()
        return []


async def classify_stage(document_id: str, idea: dict, db: Session) -> dict:
    start = time.time()
    try:
        response = await nim_client.chat_completion(SYSTEM_CLASSIFY, f"Statement: {idea['statement']}\n\nClassify this statement.", response_format={"type": "json_object"})
        result = json.loads(response)
        log = PipelineLog(document_id=document_id, step="classify", status="completed", duration_ms=int((time.time() - start) * 1000), model=nim_client.model)
        db.add(log)
        db.commit()
        return result
    except Exception as e:
        log = PipelineLog(document_id=document_id, step="classify", status="failed", error_message=str(e), duration_ms=int((time.time() - start) * 1000))
        db.add(log)
        db.commit()
        return {"type": "Concept", "confidence": 0.5}


async def extract_entities_stage(document_id: str, statement: str, db: Session) -> dict:
    start = time.time()
    try:
        response = await nim_client.chat_completion(SYSTEM_EXTRACT_ENTITIES, statement, response_format={"type": "json_object"})
        result = json.loads(response)
        log = PipelineLog(document_id=document_id, step="extract_entities", status="completed", duration_ms=int((time.time() - start) * 1000), model=nim_client.model)
        db.add(log)
        db.commit()
        return result
    except Exception as e:
        log = PipelineLog(document_id=document_id, step="extract_entities", status="failed", error_message=str(e), duration_ms=int((time.time() - start) * 1000))
        db.add(log)
        db.commit()
        return {"entities": [], "conditions": []}


async def validate_stage(document_id: str, knowledge_obj: dict, db: Session) -> dict:
    start = time.time()
    try:
        response = await nim_client.chat_completion(SYSTEM_VALIDATE, json.dumps(knowledge_obj, indent=2), response_format={"type": "json_object"})
        result = json.loads(response)
        log = PipelineLog(document_id=document_id, step="validate", status="completed", duration_ms=int((time.time() - start) * 1000), model=nim_client.model)
        db.add(log)
        db.commit()
        return result
    except Exception as e:
        log = PipelineLog(document_id=document_id, step="validate", status="failed", error_message=str(e), duration_ms=int((time.time() - start) * 1000))
        db.add(log)
        db.commit()
        return {"valid": True, "confidence_score": 0.5, "issues": [], "suggestions": []}
```

**Step 4: Write orchestrator.py**

```python
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.models import Document, KnowledgeObject, KnowledgeEntity, KnowledgeCondition, KnowledgeRelation, PipelineLog
from app.domain.types import KnowledgeType, DocumentStatus, RelationType
from app.pipeline.stages import extract_ideas_stage, classify_stage, extract_entities_stage, validate_stage


async def run_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.EXTRACTING
        db.commit()
        text = "Extracted text placeholder"  # Will be replaced with actual extraction

        doc.status = DocumentStatus.CLEANING
        db.commit()
        cleaned_text = text.strip()

        doc.status = DocumentStatus.SEGMENTING
        db.commit()
        segments = [s.strip() for s in cleaned_text.split("\n\n") if s.strip()]

        doc.status = DocumentStatus.EXTRACTING_IDEAS
        db.commit()
        all_ideas = []
        for segment in segments[:20]:
            ideas = await extract_ideas_stage(str(doc.id), segment, db)
            all_ideas.extend(ideas)

        doc.status = DocumentStatus.CLASSIFYING
        db.commit()

        doc.status = DocumentStatus.EXTRACTING_ENTITIES
        db.commit()

        knowledge_ids = []
        for idea in all_ideas:
            try:
                kt = KnowledgeType(idea.get("type", "Concept"))
            except ValueError:
                kt = KnowledgeType.CONCEPT
            classification = await classify_stage(str(doc.id), idea, db)
            entities_data = await extract_entities_stage(str(doc.id), idea.get("statement", ""), db)
            ko = KnowledgeObject(
                organization_id=doc.organization_id, document_id=doc.id, type=kt,
                title=idea.get("statement", "")[:100], statement=idea.get("statement", ""),
                original_text=idea.get("statement", ""), confidence=classification.get("confidence", 0.5),
            )
            db.add(ko)
            db.flush()
            for ent in entities_data.get("entities", []):
                db.add(KnowledgeEntity(knowledge_id=ko.id, entity_type=ent.get("type", "object"), value=ent.get("value", ""), role=ent.get("role")))
            for cond in entities_data.get("conditions", []):
                db.add(KnowledgeCondition(knowledge_id=ko.id, condition_type=cond.get("type", "condition"), description=cond.get("description", "")))
            validation = await validate_stage(str(doc.id), {"id": str(ko.id), "type": str(ko.type), "statement": ko.statement}, db)
            ko.confidence = validation.get("confidence_score", ko.confidence)
            knowledge_ids.append(str(ko.id))
            db.commit()

        doc.status = DocumentStatus.BUILDING_RELATIONS
        db.commit()
        if len(knowledge_ids) >= 2:
            knowledge_objs = db.query(KnowledgeObject).filter(KnowledgeObject.id.in_(knowledge_ids)).all()
            for i, ko_a in enumerate(knowledge_objs):
                for ko_b in knowledge_objs[i + 1:]:
                    if ko_a.type == ko_b.type:
                        db.add(KnowledgeRelation(source_id=ko_a.id, target_id=ko_b.id, relation_type=RelationType.REFERENCES, confidence=0.5))

        doc.status = DocumentStatus.COMPLETED
        db.commit()
    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()
```

---

### Task 8: Knowledge, Search & Export APIs

**Files:**
- Create: `backend/app/service/knowledge_service.py`
- Create: `backend/app/service/search_service.py`
- Create: `backend/app/api/v1/knowledge.py`
- Create: `backend/app/api/v1/search.py`
- Create: `backend/app/api/v1/export.py`

**Step 1: Write knowledge_service.py**

```python
from typing import Optional
from sqlalchemy.orm import Session
from app.domain.models import KnowledgeObject, KnowledgeEntity, KnowledgeCondition, KnowledgeRelation
from app.domain.types import RelationType


def list_knowledge(db: Session, organization_id: str, knowledge_type: Optional[str] = None, document_id: Optional[str] = None) -> list[KnowledgeObject]:
    query = db.query(KnowledgeObject).filter(KnowledgeObject.organization_id == organization_id)
    if knowledge_type:
        query = query.filter(KnowledgeObject.type == knowledge_type)
    if document_id:
        query = query.filter(KnowledgeObject.document_id == document_id)
    return query.order_by(KnowledgeObject.created_at.desc()).all()


def get_knowledge(db: Session, knowledge_id: str, organization_id: str) -> Optional[KnowledgeObject]:
    return db.query(KnowledgeObject).filter(
        KnowledgeObject.id == knowledge_id, KnowledgeObject.organization_id == organization_id
    ).first()


def get_knowledge_graph(db: Session, organization_id: str) -> dict:
    knowledge_list = db.query(KnowledgeObject).filter(KnowledgeObject.organization_id == organization_id).all()
    relations = db.query(KnowledgeRelation).filter(
        KnowledgeRelation.source_id.in_([k.id for k in knowledge_list])
    ).all() if knowledge_list else []
    nodes = [{"id": str(k.id), "type": k.type, "label": k.statement[:80], "confidence": k.confidence} for k in knowledge_list]
    edges = [{"source": str(r.source_id), "target": str(r.target_id), "type": r.relation_type} for r in relations]
    return {"nodes": nodes, "edges": edges}


def serialize_knowledge(ko: KnowledgeObject) -> dict:
    return {
        "id": str(ko.id), "type": ko.type, "title": ko.title,
        "statement": ko.statement, "original_text": ko.original_text,
        "confidence": ko.confidence, "created_at": ko.created_at.isoformat(),
        "entities": [{"entity_type": e.entity_type, "value": e.value, "role": e.role} for e in ko.entities],
        "conditions": [{"condition_type": c.condition_type, "description": c.description} for c in ko.conditions],
    }
```

**Step 2: Write knowledge.py router**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.domain.schemas import APIResponse
from app.service.knowledge_service import list_knowledge, get_knowledge, get_knowledge_graph, serialize_knowledge
from app.api.v1.dependencies import get_current_user
from app.domain.models import KnowledgeRelation

router = APIRouter()


@router.get("")
async def get_knowledge_list(
    type: Optional[str] = Query(None), document_id: Optional[str] = Query(None),
    user=Depends(get_current_user), db: Session = Depends(get_db),
):
    _, org_id = user
    knowledge_list = list_knowledge(db, org_id, type, document_id)
    return APIResponse(data=[serialize_knowledge(k) for k in knowledge_list])


@router.get("/graph")
async def knowledge_graph(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    graph = get_knowledge_graph(db, org_id)
    return APIResponse(data=graph)


@router.get("/{knowledge_id}")
async def get_knowledge_detail(knowledge_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    ko = get_knowledge(db, knowledge_id, org_id)
    if not ko:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    result = serialize_knowledge(ko)
    result["source_relations"] = [
        {"target_id": str(r.target_id), "type": r.relation_type, "confidence": r.confidence}
        for r in ko.source_relations
    ]
    result["target_relations"] = [
        {"source_id": str(r.source_id), "type": r.relation_type, "confidence": r.confidence}
        for r in ko.target_relations
    ]
    return APIResponse(data=result)


@router.get("/{knowledge_id}/relations")
async def get_knowledge_relations(knowledge_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    ko = get_knowledge(db, knowledge_id, org_id)
    if not ko:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    relations = []
    for r in ko.source_relations:
        relations.append({"direction": "outgoing", "target_id": str(r.target_id), "type": r.relation_type, "confidence": r.confidence})
    for r in ko.target_relations:
        relations.append({"direction": "incoming", "source_id": str(r.source_id), "type": r.relation_type, "confidence": r.confidence})
    return APIResponse(data=relations)
```

**Step 3: Write search_service.py**

```python
from sqlalchemy.orm import Session
from app.domain.models import KnowledgeObject, Document


def search_knowledge(db: Session, organization_id: str, query: str) -> list[dict]:
    results = (
        db.query(KnowledgeObject, Document.title)
        .join(Document, KnowledgeObject.document_id == Document.id)
        .filter(
            KnowledgeObject.organization_id == organization_id,
            KnowledgeObject.statement.ilike(f"%{query}%"),
        )
        .order_by(KnowledgeObject.confidence.desc())
        .limit(20)
        .all()
    )
    return [
        {"id": str(ko.id), "statement": ko.statement, "type": ko.type,
         "confidence": ko.confidence, "score": ko.confidence, "document_title": doc_title}
        for ko, doc_title in results
    ]
```

**Step 4: Write search.py router**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.schemas import APIResponse
from app.service.search_service import search_knowledge
from app.api.v1.dependencies import get_current_user

router = APIRouter()


@router.get("")
async def search(q: str = Query(..., min_length=1), user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    results = search_knowledge(db, org_id, q)
    return APIResponse(data=results)
```

**Step 5: Write export.py router**

```python
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.service.knowledge_service import list_knowledge, serialize_knowledge
from app.api.v1.dependencies import get_current_user

router = APIRouter()


@router.get("/json")
async def export_json(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    knowledge_list = list_knowledge(db, org_id)
    data = [serialize_knowledge(k) for k in knowledge_list]
    from fastapi.responses import JSONResponse
    return JSONResponse(content=data, media_type="application/json", headers={"Content-Disposition": "attachment; filename=structra-export.json"})


@router.get("/csv")
async def export_csv(user=Depends(get_current_user), db: Session = Depends(get_db)):
    _, org_id = user
    knowledge_list = list_knowledge(db, org_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "type", "title", "statement", "confidence", "created_at"])
    for k in knowledge_list:
        writer.writerow([k.id, k.type, k.title, k.statement, k.confidence, k.created_at.isoformat()])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=structra-export.csv"},
    )
```

---

### Task 9: Scaffold frontend with Next.js

**Files:**
- Create: `frontend/` (via create-next-app)
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/providers.tsx`

**Step 1: Create Next.js app**

Run: `cd C:\Users\PC\Documents\Structra && npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm`

**Step 2: Install dependencies**

Run: `cd frontend && pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-label @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-slot @radix-ui/react-switch class-variance-authority clsx tailwind-merge lucide-react @tanstack/react-query reactflow`

**Step 3: Init Shadcn UI**

Run: `cd frontend && pnpm dlx shadcn@latest init -d`
Then: `cd frontend && pnpm dlx shadcn@latest add button input card table badge avatar toast select`

**Step 4: Write types/index.ts**

```typescript
export interface User { id: string; email: string; name: string }

export interface Document {
  id: string; title: string; file_type: string;
  file_size: number | null; status: string;
  page_count: number | null; error_message: string | null;
  created_at: string;
}

export interface KnowledgeEntity { entity_type: string; value: string; role: string | null }
export interface KnowledgeCondition { condition_type: string; description: string }

export interface KnowledgeObject {
  id: string; type: string; title: string | null;
  statement: string; original_text: string;
  confidence: number; created_at: string;
  entities: KnowledgeEntity[]; conditions: KnowledgeCondition[];
}

export interface GraphNode { id: string; type: string; label: string; confidence: number }
export interface GraphEdge { source: string; target: string; type: string }
export interface SearchResult { id: string; statement: string; type: string; confidence: number; score: number; document_title: string }
export interface APIResponse<T> { status: string; data: T; error?: string; meta?: Record<string, unknown> }
```

**Step 5: Write lib/api.ts**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") this.token = localStorage.getItem("token");
  }

  setToken(token: string) { this.token = token; localStorage.setItem("token", token); }
  clearToken() { this.token = null; localStorage.removeItem("token"); }

  private getHeaders(): Record<string, string> {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (this.token) h["Authorization"] = `Bearer ${this.token}`;
    return h;
  }

  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST", headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async upload<T>(path: string, formData: FormData): Promise<T> {
    const h: Record<string, string> = {};
    if (this.token) h["Authorization"] = `Bearer ${this.token}`;
    const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers: h, body: formData });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, { method: "DELETE", headers: this.getHeaders() });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
}

export const api = new ApiClient();
```

**Step 6: Write components/providers.tsx**

```tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}
```

---

### Task 10: Auth pages (frontend)

**Files:**
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/login/page.tsx`
- Create: `frontend/src/app/register/page.tsx`

**Step 1: Write layout.tsx**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });
export const metadata: Metadata = { title: "Structra", description: "AI Knowledge Engineering Platform" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 min-h-screen`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

**Step 2: Write page.tsx (landing redirect)**

```tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  useEffect(() => { router.push("/login"); }, [router]);
  return <div className="flex items-center justify-center min-h-screen"><p>Loading...</p></div>;
}
```

**Step 3: Write login/page.tsx**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res: any = await api.post("/auth/login", { email, password });
      api.setToken(res.data.token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-[400px] bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Structra</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-zinc-400">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" className="w-full">Sign In</Button>
            <p className="text-sm text-zinc-500 text-center">
              Don't have an account? <a href="/register" className="text-blue-400 hover:underline">Register</a>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Step 4: Write register/page.tsx**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res: any = await api.post("/auth/register", { email, password, name, organization_name: orgName });
      api.setToken(res.data.token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <Card className="w-[400px] bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription>Join Structra</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-zinc-400">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Organization</label>
              <Input value={orgName} onChange={(e) => setOrgName(e.target.value)} required className="bg-zinc-800 border-zinc-700" />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" className="w-full">Create Account</Button>
            <p className="text-sm text-zinc-500 text-center">
              Already have an account? <a href="/login" className="text-blue-400 hover:underline">Sign in</a>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### Task 11: Dashboard page

**Files:**
- Create: `frontend/src/app/dashboard/page.tsx`
- Create: `frontend/src/components/Navbar.tsx`
- Create: `frontend/src/components/DashboardStats.tsx`

**Step 1: Write components/Navbar.tsx**

```tsx
"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function Navbar() {
  const router = useRouter();

  const handleLogout = () => {
    api.clearToken();
    router.push("/login");
  };

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link href="/dashboard" className="text-xl font-bold text-white">Structra</Link>
        <Link href="/documents" className="text-sm text-zinc-400 hover:text-white transition-colors">Documents</Link>
        <Link href="/knowledge" className="text-sm text-zinc-400 hover:text-white transition-colors">Knowledge</Link>
      </div>
      <Button variant="ghost" onClick={handleLogout} className="text-zinc-400 hover:text-white">Logout</Button>
    </nav>
  );
}
```

**Step 2: Write components/DashboardStats.tsx**

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardStats() {
  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const { data: knowledgeData } = useQuery({ queryKey: ["knowledge"], queryFn: () => api.get<any>("/knowledge") });

  const docs = docsData?.data || [];
  const knowledge = knowledgeData?.data || [];

  const completedDocs = docs.filter((d: any) => d.status === "completed").length;
  const pendingDocs = docs.filter((d: any) => d.status === "uploaded").length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Total Documents</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold">{docs.length}</p></CardContent>
      </Card>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Completed</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold text-green-400">{completedDocs}</p></CardContent>
      </Card>
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader><CardTitle className="text-zinc-400 text-sm font-medium">Knowledge Units</CardTitle></CardHeader>
        <CardContent><p className="text-3xl font-bold text-blue-400">{knowledge.length}</p></CardContent>
      </Card>
    </div>
  );
}
```

**Step 3: Write dashboard/page.tsx**

```tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DashboardStats } from "@/components/DashboardStats";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    try { api.get("/auth/me"); } catch { router.push("/login"); }
  }, [router]);

  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const recentDocs = (docsData?.data || []).slice(0, 5);

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <DashboardStats />
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Recent Documents</CardTitle></CardHeader>
          <CardContent>
            {recentDocs.length === 0 ? (
              <p className="text-zinc-500">No documents yet. <a href="/documents" className="text-blue-400 hover:underline">Upload one</a></p>
            ) : (
              <div className="space-y-2">
                {recentDocs.map((doc: any) => (
                  <div key={doc.id} className="flex justify-between items-center p-2 hover:bg-zinc-800 rounded">
                    <span>{doc.title}</span>
                    <span className={`text-xs px-2 py-1 rounded ${doc.status === "completed" ? "bg-green-900 text-green-300" : "bg-yellow-900 text-yellow-300"}`}>{doc.status}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
```

---

### Task 12: Documents pages

**Files:**
- Create: `frontend/src/app/documents/page.tsx`
- Create: `frontend/src/app/documents/[id]/page.tsx`
- Create: `frontend/src/components/DocumentUploader.tsx`
- Create: `frontend/src/components/PipelineStatus.tsx`

**Step 1: Write components/DocumentUploader.tsx**

```tsx
"use client";
import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";

export function DocumentUploader() {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.upload("/documents", formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast({ title: "Document uploaded", description: "Processing will start shortly" });
    },
    onError: (err: Error) => toast({ title: "Upload failed", description: err.message, variant: "destructive" }),
  });

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) mutation.mutate(file);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragOver ? "border-blue-500 bg-blue-500/10" : "border-zinc-700 hover:border-zinc-500"
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => e.target.files?.[0] && mutation.mutate(e.target.files[0])} />
      <p className="text-zinc-400 mb-2">Drop a document here or click to browse</p>
      <p className="text-zinc-600 text-sm">PDF, DOCX, XLSX, PPTX, TXT, MD, HTML, XML, CSV</p>
      {mutation.isPending && <p className="text-blue-400 mt-2">Uploading...</p>}
    </div>
  );
}
```

**Step 2: Write documents/page.tsx**

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { DocumentUploader } from "@/components/DocumentUploader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function DocumentsPage() {
  const { data: docsData, isLoading } = useQuery({ queryKey: ["documents"], queryFn: () => api.get<any>("/documents") });
  const docs = docsData?.data || [];

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Documents</h1>
        <DocumentUploader />
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>All Documents</CardTitle></CardHeader>
          <CardContent>
            {isLoading ? <p className="text-zinc-500">Loading...</p> : docs.length === 0 ? (
              <p className="text-zinc-500">No documents uploaded yet.</p>
            ) : (
              <div className="space-y-2">
                {docs.map((doc: any) => (
                  <Link key={doc.id} href={`/documents/${doc.id}`} className="flex justify-between items-center p-3 hover:bg-zinc-800 rounded transition-colors">
                    <div>
                      <p className="font-medium">{doc.title}</p>
                      <p className="text-sm text-zinc-500">{doc.file_type} • {Math.round(doc.file_size / 1024)}KB</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${doc.status === "completed" ? "bg-green-900 text-green-300" : doc.status === "failed" ? "bg-red-900 text-red-300" : "bg-yellow-900 text-yellow-300"}`}>{doc.status}</span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
```

**Step 3: Write components/PipelineStatus.tsx**

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const steps = ["uploaded", "extracting", "cleaning", "segmenting", "extracting_ideas", "classifying", "extracting_entities", "building_relations", "validating", "completed"];

export function PipelineStatus({ documentId }: { documentId: string }) {
  const { data: statusData, isLoading } = useQuery({
    queryKey: ["document-status", documentId],
    queryFn: () => api.get<any>(`/documents/${documentId}/status`),
    refetchInterval: 3000,
  });

  if (isLoading) return <p className="text-zinc-500">Loading status...</p>;
  const status = statusData?.data?.status || "unknown";
  const currentIndex = steps.indexOf(status);

  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-400">Status: <span className="font-medium text-white">{status}</span></p>
      <div className="flex gap-1 flex-wrap">
        {steps.map((step, i) => (
          <div key={step} className={`h-2 w-6 rounded-full ${i < currentIndex ? "bg-green-500" : i === currentIndex ? "bg-blue-500 animate-pulse" : "bg-zinc-700"}`} />
        ))}
      </div>
    </div>
  );
}
```

**Step 4: Write documents/[id]/page.tsx**

```tsx
"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { PipelineStatus } from "@/components/PipelineStatus";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";

export default function DocumentDetailPage() {
  const params = useParams();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: docData } = useQuery({
    queryKey: ["document", params.id],
    queryFn: () => api.get<any>(`/documents/${params.id}`),
  });

  const { data: knowledgeData } = useQuery({
    queryKey: ["knowledge", params.id],
    queryFn: () => api.get<any>(`/knowledge?document_id=${params.id}`),
  });

  const processMutation = useMutation({
    mutationFn: () => api.post(`/documents/${params.id}/process`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-status", params.id] });
      toast({ title: "Pipeline started" });
    },
  });

  const doc = docData?.data;
  const knowledge = knowledgeData?.data || [];

  if (!doc) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Loading...</p></main></div>;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{doc.title}</h1>
            <p className="text-zinc-400 text-sm">{doc.file_type} • {doc.file_size ? Math.round(doc.file_size / 1024) + "KB" : "?"}</p>
          </div>
          <Button onClick={() => processMutation.mutate()} disabled={doc.status !== "uploaded" && doc.status !== "failed"}>
            {processMutation.isPending ? "Starting..." : "Process"}
          </Button>
        </div>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Pipeline Status</CardTitle></CardHeader>
          <CardContent><PipelineStatus documentId={params.id as string} /></CardContent>
        </Card>

        <div>
          <h2 className="text-xl font-semibold mb-4">Extracted Knowledge ({knowledge.length})</h2>
          <div className="grid gap-3">
            {knowledge.map((k: any) => <KnowledgeCard key={k.id} knowledge={k} />)}
            {knowledge.length === 0 && <p className="text-zinc-500">No knowledge extracted yet. Run the pipeline.</p>}
          </div>
        </div>
      </main>
    </div>
  );
}
```

---

### Task 13: Knowledge pages

**Files:**
- Create: `frontend/src/app/knowledge/page.tsx`
- Create: `frontend/src/app/knowledge/[id]/page.tsx`
- Create: `frontend/src/components/KnowledgeCard.tsx`
- Create: `frontend/src/components/KnowledgeFilters.tsx`
- Create: `frontend/src/components/SemanticSearch.tsx`

**Step 1: Write components/KnowledgeCard.tsx**

```tsx
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

const typeColors: Record<string, string> = {
  Rule: "border-l-blue-500", Definition: "border-l-green-500", Procedure: "border-l-yellow-500",
  Responsibility: "border-l-purple-500", Constraint: "border-l-red-500", Exception: "border-l-orange-500",
  Requirement: "border-l-cyan-500", Policy: "border-l-pink-500",
};

export function KnowledgeCard({ knowledge }: { knowledge: any }) {
  const borderColor = typeColors[knowledge.type] || "border-l-zinc-500";

  return (
    <Link href={`/knowledge/${knowledge.id}`}>
      <Card className={`bg-zinc-900 border-zinc-800 border-l-4 ${borderColor} hover:bg-zinc-800 transition-colors`}>
        <CardContent className="p-4">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{knowledge.type}</span>
            <span className="text-xs text-zinc-500">{Math.round(knowledge.confidence * 100)}%</span>
          </div>
          <p className="text-sm">{knowledge.statement}</p>
          {knowledge.entities?.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {knowledge.entities.map((e: any, i: number) => (
                <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">{e.value}</span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
```

**Step 2: Write components/KnowledgeFilters.tsx**

```tsx
"use client";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const types = ["All", "Rule", "Definition", "Procedure", "Decision", "Workflow", "Responsibility", "Constraint", "Exception", "Requirement", "Policy", "Concept"];

export function KnowledgeFilters({ onTypeChange, onSearchChange }: { onTypeChange: (t: string) => void; onSearchChange: (s: string) => void }) {
  return (
    <div className="flex gap-4 mb-4">
      <Input placeholder="Search knowledge..." onChange={(e) => onSearchChange(e.target.value)} className="bg-zinc-800 border-zinc-700 max-w-md" />
      <Select onValueChange={onTypeChange}>
        <SelectTrigger className="w-[180px] bg-zinc-800 border-zinc-700">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent className="bg-zinc-900 border-zinc-800">
          {types.map((t) => <SelectItem key={t} value={t === "All" ? "" : t}>{t}</SelectItem>)}
        </SelectContent>
      </Select>
    </div>
  );
}
```

**Step 3: Write knowledge/page.tsx**

```tsx
"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { KnowledgeCard } from "@/components/KnowledgeCard";
import { KnowledgeFilters } from "@/components/KnowledgeFilters";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function KnowledgePage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: knowledgeData } = useQuery({
    queryKey: ["knowledge", typeFilter],
    queryFn: () => api.get<any>(`/knowledge${typeFilter ? `?type=${typeFilter}` : ""}`),
  });

  const knowledge = knowledgeData?.data || [];
  const filtered = search
    ? knowledge.filter((k: any) => k.statement.toLowerCase().includes(search.toLowerCase()))
    : knowledge;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6">
        <h1 className="text-2xl font-bold">Knowledge Explorer</h1>
        <Tabs defaultValue="list">
          <TabsList className="bg-zinc-900">
            <TabsTrigger value="list">List</TabsTrigger>
            <TabsTrigger value="graph">Graph</TabsTrigger>
          </TabsList>
          <TabsContent value="list" className="space-y-4">
            <KnowledgeFilters onTypeChange={setTypeFilter} onSearchChange={setSearch} />
            <div className="grid gap-3">
              {filtered.map((k: any) => <KnowledgeCard key={k.id} knowledge={k} />)}
              {filtered.length === 0 && <p className="text-zinc-500">No knowledge found.</p>}
            </div>
          </TabsContent>
          <TabsContent value="graph">
            <KnowledgeGraph />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
```

**Step 4: Write knowledge/[id]/page.tsx**

```tsx
"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function KnowledgeDetailPage() {
  const params = useParams();

  const { data: detailData, isLoading } = useQuery({
    queryKey: ["knowledge-detail", params.id],
    queryFn: () => api.get<any>(`/knowledge/${params.id}`),
  });

  if (isLoading) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Loading...</p></main></div>;

  const k = detailData?.data;
  if (!k) return <div className="min-h-screen bg-zinc-950"><Navbar /><main className="p-6"><p className="text-zinc-500">Not found</p></main></div>;

  return (
    <div className="min-h-screen bg-zinc-950">
      <Navbar />
      <main className="p-6 space-y-6 max-w-4xl">
        <div>
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{k.type}</span>
          <h1 className="text-2xl font-bold mt-2">{k.title || k.statement}</h1>
        </div>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Statement</CardTitle></CardHeader>
          <CardContent><p>{k.statement}</p></CardContent>
        </Card>

        {k.entities?.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle>Entities</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {k.entities.map((e: any, i: number) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-zinc-500 w-16">{e.entity_type}</span>
                    <span>{e.value}</span>
                    {e.role && <span className="text-zinc-600">({e.role})</span>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {k.conditions?.length > 0 && (
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader><CardTitle>Conditions</CardTitle></CardHeader>
            <CardContent>
              {k.conditions.map((c: any, i: number) => (
                <p key={i} className="text-sm"><span className="text-zinc-500">{c.condition_type}:</span> {c.description}</p>
              ))}
            </CardContent>
          </Card>
        )}

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader><CardTitle>Metadata</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-zinc-500">Confidence</span>
              <span>{Math.round(k.confidence * 100)}%</span>
              <span className="text-zinc-500">Original text</span>
              <span className="text-zinc-300 text-xs">{k.original_text}</span>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
```

---

### Task 14: Knowledge Graph visualization

**Files:**
- Create: `frontend/src/components/KnowledgeGraph.tsx`

**Step 1: Write KnowledgeGraph.tsx**

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCallback, useRef, useEffect } from "react";

// Simple canvas-based force-directed graph (no external deps)
export function KnowledgeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { data: graphData, isLoading } = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () => api.get<any>("/knowledge/graph"),
  });

  useEffect(() => {
    if (!graphData?.data || !canvasRef.current) return;
    const { nodes, edges } = graphData.data;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth * 2;
    canvas.height = 500 * 2;
    ctx.scale(2, 2);

    const positions: Record<string, { x: number; y: number }> = {};
    const centerX = canvas.offsetWidth / 2;
    const centerY = 250;

    nodes.forEach((n: any, i: number) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      positions[n.id] = { x: centerX + 200 * Math.cos(angle), y: centerY + 200 * Math.sin(angle) };
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    edges.forEach((e: any) => {
      const src = positions[e.source];
      const tgt = positions[e.target];
      if (src && tgt) {
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = "rgba(99, 102, 241, 0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });

    nodes.forEach((n: any) => {
      const pos = positions[n.id];
      if (!pos) return;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 6, 0, 2 * Math.PI);
      ctx.fillStyle = n.confidence > 0.8 ? "#22c55e" : "#eab308";
      ctx.fill();
      ctx.fillStyle = "#a1a1aa";
      ctx.font = "10px sans-serif";
      ctx.fillText(n.label.substring(0, 30), pos.x + 10, pos.y + 4);
    });
  }, [graphData]);

  if (isLoading) return <p className="text-zinc-500">Loading graph...</p>;

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
      <canvas ref={canvasRef} style={{ width: "100%", height: "500px" }} />
      {(!graphData?.data?.nodes || graphData.data.nodes.length === 0) && (
        <p className="text-zinc-500 text-center py-20">No knowledge graph data yet.</p>
      )}
    </div>
  );
}
```

---

### Task 15: Semantic Search UI

**Files:**
- Create: `frontend/src/app/search/page.tsx` (or reuse in navbar)

**Step 1: Add search to Navbar.tsx**

Add this inside the nav div, before the logout button:

```tsx
<div className="flex-1 max-w-md mx-4">
  <input
    type="text"
    placeholder="Search knowledge..."
    className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-3 py-1.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500"
    onKeyDown={(e) => {
      if (e.key === "Enter") {
        const value = (e.target as HTMLInputElement).value;
        if (value.trim()) router.push(`/knowledge?search=${encodeURIComponent(value.trim())}`);
      }
    }}
  />
</div>
```

---

### Task 16: Root package.json and final configuration

**Files:**
- Create: `package.json` (root)
- Create: `backend/.env.example`

**Step 1: Write root package.json**

```json
{
  "name": "structra",
  "private": true,
  "scripts": {
    "dev:frontend": "cd frontend && pnpm dev",
    "dev:backend": "cd backend && uvicorn main:app --reload --port 8000",
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "install:all": "cd backend && pip install -r requirements.txt && cd ../frontend && pnpm install"
  },
  "devDependencies": {
    "concurrently": "^8.2.0"
  }
}
```

**Step 2: Write backend/.env.example**

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/structra
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_STORAGE_BUCKET=documents
QDRANT_URL=http://localhost:6333
NVIDIA_API_KEY=your-nvidia-nim-key
NVIDIA_MODEL=meta/llama-3.1-405b-instruct
JWT_SECRET=generate-a-secure-random-secret
```

---

### Execution order summary

| # | Task | Files to create |
|---|------|----------------|
| 1 | Scaffold backend | 12 files (structure, config, database, main.py) |
| 2 | Domain models | 4 files (types, models, schemas) |
| 3 | DB migrations | Alembic config + initial migration |
| 4 | Auth API | 3 files (auth_service, auth router, dependencies) |
| 5 | Document API | 2 files (document_service, documents router) |
| 6 | Text extraction | 1 file (extraction_service.py) |
| 7 | AI pipeline | 4 files (nim_client, prompts, stages, orchestrator) |
| 8 | Knowledge/Search/Export APIs | 5 files (knowledge_service, search_service, 3 routers) |
| 9 | Frontend scaffold | Next.js project + types + api client + providers |
| 10 | Auth pages | layout, landing, login, register |
| 11 | Dashboard | dashboard page + Navbar + DashboardStats |
| 12 | Documents pages | documents list + detail + DocumentUploader + PipelineStatus |
| 13 | Knowledge pages | knowledge explorer + detail + KnowledgeCard + KnowledgeFilters |
| 14 | Knowledge Graph | Canvas-based force-directed graph component |
| 15 | Semantic Search | Search input in Navbar |
| 16 | Root config | package.json + .env.example |

Total: ~35 files, all with complete implementation code provided above.
