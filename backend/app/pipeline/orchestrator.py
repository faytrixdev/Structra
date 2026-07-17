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
        text = "Extracted text placeholder"

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
