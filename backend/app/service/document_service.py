import hashlib
import uuid
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.models import Document, AuditLog
from app.domain.types import DocumentStatus

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


async def upload_document(db: Session, organization_id: str, user_id: str, file: UploadFile, content: bytes) -> Document:
    if file.content_type not in settings.allowed_file_types:
        raise ValueError(f"File type {file.content_type} not supported")
    file_size = len(content)
    if file_size > settings.max_file_size_mb * 1024 * 1024:
        raise ValueError(f"File exceeds {settings.max_file_size_mb}MB limit")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}-{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)

    content_hash = hashlib.sha256(content).hexdigest()

    doc = Document(
        organization_id=organization_id, title=file.filename or "untitled",
        file_type=file.content_type or "application/octet-stream",
        file_path=file_path, file_size=file_size, content_hash=content_hash,
        status=DocumentStatus.UPLOADED,
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
