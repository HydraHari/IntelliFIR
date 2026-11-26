"""
ml/embeddings/embedding_service.py — Sentence embedding via sentence-transformers.

Produces normalized L2 embeddings suitable for cosine similarity with FAISS IndexFlatIP.
"""
from __future__ import annotations

import logging
import threading
from typing import List, Optional

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

_LOAD_LOCK = threading.Lock()


class EmbeddingService:
    """
    Wraps sentence-transformers SentenceTransformer to produce fixed-dimension
    normalized embeddings.
    """

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._load_error: Optional[str] = None

    def load(self) -> None:
        """Thread-safe model loading."""
        with _LOAD_LOCK:
            if self._model is not None:
                return
            if self._load_error is not None:
                raise RuntimeError(self._load_error)
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model: %s", self.model_name)
                self._model = SentenceTransformer(
                    self.model_name, cache_folder=settings.MODELS_CACHE_DIR
                )
                logger.info("Embedding model loaded successfully.")
            except Exception as exc:
                self._load_error = (
                    f"Failed to load embedding model '{self.model_name}': {exc}"
                )
                logger.error(self._load_error)
                raise RuntimeError(self._load_error) from exc

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string.

        :returns: Normalized float32 numpy array of shape (dimension,).
        """
        if self._model is None:
            self.load()
        vec = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed a list of texts.

        :returns: Normalized float32 numpy array of shape (n, dimension).
        """
        if self._model is None:
            self.load()
        vecs = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vecs.astype(np.float32)

    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors."""
        return float(np.dot(vec_a, vec_b))


# Module-level singleton
embedding_service = EmbeddingService()
