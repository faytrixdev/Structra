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
    nvidia_model: str = "meta/llama-3.1-70b-instruct"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    pipeline_mode: str = "high_accuracy"
    pipeline_max_concurrency: int = 2
    pipeline_idea_batch_size: int = 50
    pipeline_classify_concurrency: int = 2
    pipeline_entity_concurrency: int = 2
    pipeline_request_pacing_ms: int = 1500
    # Combine classify + entity extraction into a single LLM call per idea.
    # Halves request count on rate-limited providers like NVIDIA NIM free tier.
    pipeline_combined_default: bool = True
    # If True, retry once with exponential backoff when NIM returns 429.
    pipeline_retry_on_429: bool = True

    # ── CORS ─────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # In production set to your Vercel URL: https://your-app.vercel.app
    cors_origins: str = "http://localhost:3000"

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

    @property
    def cors_origins_list(self) -> list[str]:
        """Split CORS_ORIGINS into a list, stripping whitespace."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
