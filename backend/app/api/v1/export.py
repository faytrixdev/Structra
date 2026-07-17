import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
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
