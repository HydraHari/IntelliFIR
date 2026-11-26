"""
ml/config.py — ML model configuration singleton.
"""
from __future__ import annotations

from app.core.config import settings


class MLConfig:
    """Central ML configuration derived from app settings."""

    NER_MODEL_CHECKPOINT: str = settings.NER_MODEL_CHECKPOINT
    EMBEDDING_MODEL: str = settings.EMBEDDING_MODEL
    EMBEDDING_DIMENSION: int = settings.EMBEDDING_DIMENSION
    FAISS_INDEX_PATH: str = settings.FAISS_INDEX_PATH
    MODELS_CACHE_DIR: str = settings.MODELS_CACHE_DIR
    SIMILARITY_THRESHOLD: float = settings.SIMILARITY_THRESHOLD
    SIMILAR_CASES_TOP_K: int = settings.SIMILAR_CASES_TOP_K


ml_config = MLConfig()
