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
