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
