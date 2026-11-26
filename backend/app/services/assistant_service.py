"""
services/assistant_service.py — Investigation Assistant powered by RAG and Citations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ml.rag.rag_pipeline import RAGPipeline
from app.ml.embeddings.embedding_service import embedding_service
from app.ml.llm.ollama_provider import ollama_provider
from app.services.similar_case_service import case_vector_store
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize singleton RAG pipeline
rag_pipeline = RAGPipeline(
    embedder=embedding_service,
    vector_store=case_vector_store,
    llm_provider=ollama_provider,
    top_k=5,
    similarity_threshold=0.3,
)


def query_investigation_assistant(
    question: str,
    complaint_context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute grounded RAG query for legal/investigation question.
    """
    case_vector_store._ensure_loaded()

    # If vector store is empty and no complaint context provided
    if case_vector_store.total_vectors == 0 and not complaint_context:
        return {
            "answer": (
                "Legal retrieval and vector database are not configured with reference documents yet. "
                "Add verified legal statutes or historical cases to enable retrieval-augmented investigation."
            ),
            "sources": [],
            "citations": [],
            "is_retrieval_only": True,
        }

    try:
        result = rag_pipeline.query(
            question=question,
            complaint_text=complaint_context,
        )
        return result
    except Exception as exc:
        logger.warning("RAG query failed with LLM, falling back to retrieval only: %s", exc)
        # Search vector store directly
        q_vec = embedding_service.embed(question)
        matches = case_vector_store.search(q_vec, k=3, threshold=0.2)
        sources = [
            {
                "title": m.get("title") or m.get("reference_id", "Reference Doc"),
                "content": m.get("content") or m.get("summary", ""),
                "score": round(float(m.get("score", 0.0)), 4),
            }
            for m in matches
        ]

        if not sources and complaint_context:
            sources.append({
                "title": "Current Complaint Statement",
                "content": complaint_context[:500] + "...",
                "score": 1.0,
            })

        return {
            "answer": (
                "LLM inference is currently unavailable or in retrieval-only mode. "
                "Review the retrieved verified sources and case facts below for your investigation."
            ),
            "sources": sources,
            "citations": [f"[{i+1}] {s['title']}" for i, s in enumerate(sources)],
            "is_retrieval_only": True,
        }
