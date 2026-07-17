from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Structra"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/structra"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = "documents"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_embeddings"

    nvidia_api_key: str = ""
    nvidia_model: str = "meta/llama-3.1-405b-instruct"
    nvidia_base_url: str = "https://api.nvcf.nvidia.com/v2/chat/completions"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    max_file_size_mb: int = 50
    allowed_file_types: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/markdown",
        "text/html",
        "text/xml",
        "text/csv",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
