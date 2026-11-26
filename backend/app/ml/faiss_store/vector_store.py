"""
ml/faiss_store/vector_store.py — FAISS-backed vector store for similarity search.

Uses IndexFlatIP (inner product) over L2-normalized embeddings to achieve
cosine similarity. Metadata is stored as a parallel JSON sidecar file.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_STORE_LOCK = threading.Lock()


class FAISSVectorStore:
    """
    Thread-safe FAISS vector store with persistence.

    Stores embeddings in a FAISS IndexFlatIP index (cosine similarity via
    normalized vectors) and metadata in a parallel JSON file.
    """

    INDEX_FILENAME = "index.bin"
    METADATA_FILENAME = "metadata.json"

    def __init__(self, index_path: str, dimension: int = 384):
        self.index_path = Path(index_path)
        self.dimension = dimension
        self._index = None
        self._metadata: List[dict] = []  # Parallel array to FAISS rows
        self._initialized = False

    def load_or_create(self) -> None:
        """Load existing index from disk or create a new empty one."""
        with _STORE_LOCK:
            try:
                import faiss
            except ImportError as exc:
                raise RuntimeError(
                    "faiss-cpu is required. Install it with: pip install faiss-cpu"
                ) from exc

            index_file = self.index_path / self.INDEX_FILENAME
            meta_file = self.index_path / self.METADATA_FILENAME

            if index_file.exists() and meta_file.exists():
                logger.info("Loading FAISS index from %s", index_file)
                self._index = faiss.read_index(str(index_file))
                with open(meta_file, "r", encoding="utf-8") as fh:
                    self._metadata = json.load(fh)
                logger.info(
                    "FAISS index loaded: %d vectors, dimension=%d",
                    self._index.ntotal,
                    self.dimension,
                )
            else:
                logger.info(
                    "Creating new FAISS IndexFlatIP (dimension=%d)", self.dimension
                )
                self._index = faiss.IndexFlatIP(self.dimension)
                self._metadata = []

            self._initialized = True

    def _ensure_loaded(self) -> None:
        if not self._initialized:
            self.load_or_create()

    def add(self, embedding: np.ndarray, metadata: dict) -> int:
        """
        Add a single embedding with associated metadata.

        :param embedding: 1-D float32 numpy array (should be L2-normalized).
        :param metadata:  Arbitrary metadata dict stored alongside the vector.
        :returns:         The FAISS position (row index) of the new vector.
        """
        self._ensure_loaded()
        with _STORE_LOCK:
            vec = embedding.reshape(1, -1).astype(np.float32)
            # Normalize if not already unit-length
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            position = self._index.ntotal
            self._index.add(vec)
            self._metadata.append(metadata)
            self.save()
            return int(position)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[dict]:
        """
        Search for top-k nearest neighbors.

        :param query_embedding: 1-D float32 numpy array.
        :param k:               Number of results to return.
        :param threshold:       Minimum similarity score (0-1). None = no filter.
        :returns:               List of dicts with keys: metadata, score, index.
        """
        self._ensure_loaded()
        with _STORE_LOCK:
            if self._index.ntotal == 0:
                return []

            vec = query_embedding.reshape(1, -1).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            actual_k = min(k, self._index.ntotal)
            scores, indices = self._index.search(vec, actual_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                if threshold is not None and float(score) < threshold:
                    continue
                result = dict(self._metadata[idx])
                result["score"] = float(score)
                result["faiss_index"] = int(idx)
                results.append(result)

            return results

    def save(self) -> None:
        """Persist index and metadata to disk. Called automatically on add()."""
        import faiss

        self.index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path / self.INDEX_FILENAME))
        with open(self.index_path / self.METADATA_FILENAME, "w", encoding="utf-8") as fh:
            json.dump(self._metadata, fh, ensure_ascii=False, default=str)

    @property
    def total_vectors(self) -> int:
        """Return total number of vectors in the index."""
        self._ensure_loaded()
        return self._index.ntotal if self._index else 0

    def __len__(self) -> int:
        return self.total_vectors
