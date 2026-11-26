"""
services/similar_case_service.py — Case embedding, FAISS indexing, and semantic similarity retrieval.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.legal import SimilarCase
from app.ml.embeddings.embedding_service import embedding_service
from app.ml.faiss_store.vector_store import FAISSVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize cases vector store
case_vector_store = FAISSVectorStore(
    index_path=settings.FAISS_INDEX_PATH,
    dimension=settings.EMBEDDING_DIMENSION,
)


def ingest_case(
    db: Session,
    reference_id: str,
    summary: str,
    category: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> SimilarCase:
    """
    Compute embedding for a case, add to FAISS index, and persist to database.
    """
    case_vector_store._ensure_loaded()

    # 1. Compute embedding
    vec = embedding_service.embed(summary)

    # 2. Add to FAISS
    faiss_meta = {
        "reference_id": reference_id,
        "summary": summary,
        "category": category,
        "type": "case",
    }
    pos = case_vector_store.add(vec, faiss_meta)

    # 3. Save to database
    case_obj = SimilarCase(
        reference_id=reference_id,
        summary=summary,
        category=category,
        embedding_id=pos,
        metadata_=metadata or {},
    )
    db.add(case_obj)
    db.commit()
    db.refresh(case_obj)

    return case_obj


def search_similar_cases(
    db: Session,
    query_text: str,
    top_k: int = 5,
    threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Search for similar cases using sentence embeddings and FAISS vector index.
    """
    case_vector_store._ensure_loaded()
    if case_vector_store.total_vectors == 0:
        return []

    q_vec = embedding_service.embed(query_text)
    thresh = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
    matches = case_vector_store.search(q_vec, k=top_k, threshold=thresh)

    results = []
    for m in matches:
        if m.get("type") == "case" or "reference_id" in m:
            results.append({
                "reference_id": m.get("reference_id"),
                "summary": m.get("summary"),
                "category": m.get("category"),
                "score": round(float(m.get("score", 0.0)), 4),
            })

    return results
