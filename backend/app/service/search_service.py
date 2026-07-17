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
