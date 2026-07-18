from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import auth, documents, knowledge, search, export
from app.dedup.bootstrap import bootstrap_dedup_models

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])


@app.on_event("startup")
async def startup_event():
    bootstrap_dedup_models()


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
