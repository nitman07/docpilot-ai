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

    log_level: str = "INFO"
    log_json: bool = False


settings = Settings()
