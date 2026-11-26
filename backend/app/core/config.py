"""
core/config.py — Application settings via Pydantic BaseSettings.
All values are read from environment variables or .env file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "IntelliFIR"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DEMO_MODE: bool = False

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://intellifir:intellifir@localhost:5432/intellifir",
        description="SQLAlchemy database URL (psycopg2 or asyncpg)",
    )

    # ------------------------------------------------------------------ #
    # Security
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32",
        description="JWT signing secret — override in production",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ------------------------------------------------------------------ #
    # File uploads
    # ------------------------------------------------------------------ #
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "image/jpeg",
        "image/png",
        "text/plain",
    ]

    # ------------------------------------------------------------------ #
    # ML / NER
    # ------------------------------------------------------------------ #
    NER_MODEL_CHECKPOINT: str = "dslim/bert-base-NER"
    MODELS_CACHE_DIR: str = str(BASE_DIR / "models_cache")

    # ------------------------------------------------------------------ #
    # Embeddings
    # ------------------------------------------------------------------ #
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ------------------------------------------------------------------ #
    # FAISS
    # ------------------------------------------------------------------ #
    FAISS_INDEX_PATH: str = str(BASE_DIR / "faiss_index")

    # ------------------------------------------------------------------ #
    # Ollama / LLM
    # ------------------------------------------------------------------ #
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    LLM_PROVIDER: Literal["ollama", "none"] = "ollama"
    LLM_TIMEOUT_SECONDS: int = 120

    # ------------------------------------------------------------------ #
    # Similarity search
    # ------------------------------------------------------------------ #
    SIMILARITY_THRESHOLD: float = 0.5
    SIMILAR_CASES_TOP_K: int = 5

    # ------------------------------------------------------------------ #
    # Computed properties
    # ------------------------------------------------------------------ #
    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def ensure_upload_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("FAISS_INDEX_PATH", mode="before")
    @classmethod
    def ensure_faiss_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("MODELS_CACHE_DIR", mode="before")
    @classmethod
    def ensure_models_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings: Settings = get_settings()
