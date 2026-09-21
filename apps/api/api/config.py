from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    environment: str = "development"
    secret_key: str = "change-me-in-env"
    access_token_expire_minutes: int = 60 * 12

    # Super admin bootstrap
    superadmin_username: str = "admin"
    superadmin_password: str = "change-me"

    # Postgres
    database_url: str = (
        "postgresql+psycopg://nbcc:nbcc@localhost:5432/nbcc"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    embedding_dim: int = 768

    # Storage
    storage_dir: str = "/data/documents"

    # Web origin for CORS
    web_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
