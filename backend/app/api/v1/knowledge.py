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
