from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "DocPilot"
    app_version: str = "0.1.0"
    debug: bool = False

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: str | None = None
    qdrant_prefer_grpc: bool = False

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "docpilot"
    postgres_password: str = "docpilot"
    postgres_db: str = "docpilot"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0

    openai_api_key: str = ""

    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_device: str = "cpu"

    ollama_host: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2:3b"

    log_level: str = "INFO"
    log_json: bool = False

    jwt_secret_key: str = "docpilot-dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    admin_email: str = "admin@docpilot.ai"
    admin_password: str = "admin123"


settings = Settings()
