from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.schemas import RegisterRequest, LoginRequest, APIResponse
from app.service.auth_service import register_user, authenticate_user
from app.api.v1.dependencies import get_current_user

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_user(db, req.email, req.password, req.name, req.organization_name)
        return APIResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = authenticate_user(db, req.email, req.password)
        return APIResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def me(user=Depends(get_current_user)):
    current_user, _ = user
    return APIResponse(data={"id": str(current_user.id), "email": current_user.email, "name": current_user.name})
