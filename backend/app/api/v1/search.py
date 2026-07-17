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
