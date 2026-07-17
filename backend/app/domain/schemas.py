from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class APIResponse(BaseModel):
    status: str = "success"
    data: Optional[dict | list] = None
    error: Optional[str] = None
    meta: Optional[dict] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    organization_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_type: str
    file_size: Optional[int] = None
    status: str
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class EntityResponse(BaseModel):
    entity_type: str
    value: str
    role: Optional[str] = None


class ConditionResponse(BaseModel):
    condition_type: str
    description: str


class KnowledgeResponse(BaseModel):
    id: UUID
    type: str
    title: Optional[str] = None
    statement: str
    original_text: str
    confidence: float
    entities: list[EntityResponse] = []
    conditions: list[ConditionResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    nodes: list
    edges: list


class SearchResult(BaseModel):
    id: UUID
    statement: str
    type: str
    confidence: float
    score: float
    document_title: str
