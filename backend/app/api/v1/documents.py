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
