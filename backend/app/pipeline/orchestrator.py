from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.models import Document, KnowledgeObject, KnowledgeEntity, KnowledgeCondition, KnowledgeRelation, PipelineLog
from app.domain.types import KnowledgeType, DocumentStatus, RelationType
from app.pipeline.stages import extract_ideas_stage, classify_stage, extract_entities_stage, validate_stage
from app.service.extraction_service import extract_text
from app.dedup import deduplicate


async def run_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.EXTRACTING
        db.commit()

        with open(doc.file_path, "rb") as f:
            file_content = f.read()
        text, page_count = await extract_text(doc.file_path, doc.file_type, file_content)
        doc.page_count = page_count
        db.commit()

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

        if not all_ideas:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No ideas extracted from document"
            db.commit()
            return

        doc.status = DocumentStatus.CLASSIFYING
        db.commit()

        doc.status = DocumentStatus.EXTRACTING_ENTITIES
        db.commit()

        # === Build all candidate knowledge objects in memory (no persistence yet) ===
        candidate_pairs: list[dict] = []
        for idea in all_ideas:
            try:
                kt = KnowledgeType(idea.get("type", "Concept"))
            except ValueError:
                kt = KnowledgeType.CONCEPT
            classification = await classify_stage(str(doc.id), idea, db)
            entities_data = await extract_entities_stage(str(doc.id), idea.get("statement", ""), db)
            candidate_pairs.append({
                "id": idea.get("id", str(len(candidate_pairs))),
                "type": str(kt),
                "title": idea.get("statement", "")[:100],
                "statement": idea.get("statement", ""),
                "original_text": idea.get("statement", ""),
                "confidence": classification.get("confidence", 0.5),
                "entities": entities_data.get("entities", []),
                "conditions": entities_data.get("conditions", []),
            })

        # === Deduplicate before persistence (semantic deduplication) ===
        dedup_result = deduplicate(candidate_pairs)

        # === Persist only the unique, merged results ===
        knowledge_ids = []
        for item in dedup_result:
            try:
                kt = KnowledgeType(item.get("type", "Concept"))
            except ValueError:
                kt = KnowledgeType.CONCEPT
            ko = KnowledgeObject(
                organization_id=doc.organization_id, document_id=doc.id, type=kt,
                title=item.get("statement", "")[:100], statement=item.get("statement", ""),
                original_text=item.get("original_text", ""), confidence=item.get("confidence", 0.5),
                extra_data=item.get("metadata", {}),
            )
            db.add(ko)
            db.flush()
            for ent in item.get("entities", []):
                db.add(KnowledgeEntity(knowledge_id=ko.id, entity_type=ent.get("type", "object"), value=ent.get("value", ""), role=ent.get("role")))
            for cond in item.get("conditions", []):
                db.add(KnowledgeCondition(knowledge_id=ko.id, condition_type=cond.get("type", "condition"), description=cond.get("description", "")))
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
