"""
ml/rag/rag_pipeline.py — Retrieval-Augmented Generation pipeline.

Workflow:
  1. Embed the user question.
  2. Retrieve top-k documents from FAISS (legal docs + similar cases).
  3. Build a grounded context string with citations.
  4. Send to LLM with a strict grounding system prompt.
  5. Return: answer, sources list, citations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.ml.embeddings.embedding_service import EmbeddingService
from app.ml.faiss_store.vector_store import FAISSVectorStore
from app.ml.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a legal assistant AI specialized in Indian criminal law and FIR (First Information Report) drafting.

STRICT RULES:
1. Answer ONLY using information from the provided context documents.
2. If the context does not contain enough information, say "I do not have sufficient information in the provided documents to answer this question."
3. Do NOT invent legal provisions, case citations, or facts.
4. Always cite the specific source document number (e.g., [Source 1]) when you use information from it.
5. Use formal, precise legal language.
6. Never speculate about case outcomes or legal liability.
"""

_FALLBACK_PROMPT = (
    "Based on the retrieved documents below, please answer the question.\n\n"
)


class RAGPipeline:
    """
    RAG pipeline that retrieves grounding documents and generates answers
    with strict hallucination controls.
    """

    def __init__(
        self,
        embedder: EmbeddingService,
        vector_store: FAISSVectorStore,
        llm_provider: LLMProvider,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def query(
        self,
        question: str,
        context_complaint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the RAG pipeline.

        :param question:            User's question.
        :param context_complaint_id: Optional complaint ID to bias retrieval context.
        :returns: Dict with keys: answer, sources, citations, retrieved_count.
        """
        # 1. Embed question
        try:
            query_vec = self.embedder.embed(question)
        except Exception as exc:
            logger.error("Embedding failed: %s", exc)
            return {
                "answer": "Embedding service unavailable. Please try again later.",
                "sources": [],
                "citations": [],
                "retrieved_count": 0,
                "error": str(exc),
            }

        # 2. Retrieve documents
        try:
            results = self.vector_store.search(
                query_vec, k=self.top_k, threshold=self.similarity_threshold
            )
        except Exception as exc:
            logger.error("FAISS search failed: %s", exc)
            results = []

        # 3. Build context
        sources: List[Dict[str, Any]] = []
        context_parts: List[str] = []

        for i, hit in enumerate(results, start=1):
            title = hit.get("title", f"Document {i}")
            snippet = hit.get("content_snippet", hit.get("summary", ""))
            score = hit.get("score", 0.0)
            source_ref = hit.get("source", "Unknown")

            sources.append(
                {
                    "index": i,
                    "title": title,
                    "source": source_ref,
                    "score": round(score, 4),
                    "snippet": snippet[:200] if snippet else "",
                }
            )
            context_parts.append(
                f"[Source {i}] {title} (from: {source_ref})\n{snippet}\n"
            )

        context_text = "\n---\n".join(context_parts) if context_parts else ""

        # 4. Generate answer
        if not self.llm_provider.is_available():
            # Fallback: return retrieved documents without LLM synthesis
            answer = self._fallback_answer(question, sources)
            return {
                "answer": answer,
                "sources": sources,
                "citations": [f"[Source {s['index']}]" for s in sources],
                "retrieved_count": len(results),
                "llm_used": False,
            }

        prompt = self._build_prompt(question, context_text)
        try:
            answer = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=1024,
            )
        except Exception as exc:
            logger.warning("LLM generation failed: %s — using fallback", exc)
            answer = self._fallback_answer(question, sources)
            return {
                "answer": answer,
                "sources": sources,
                "citations": [f"[Source {s['index']}]" for s in sources],
                "retrieved_count": len(results),
                "llm_used": False,
                "llm_error": str(exc),
            }

        # Extract citation references mentioned in the answer
        citations = []
        for s in sources:
            if f"[Source {s['index']}]" in answer:
                citations.append(f"[Source {s['index']}] {s['title']}")

        return {
            "answer": answer,
            "sources": sources,
            "citations": citations,
            "retrieved_count": len(results),
            "llm_used": True,
        }

    def _build_prompt(self, question: str, context: str) -> str:
        if context:
            return (
                f"Context documents:\n\n{context}\n\n"
                f"Question: {question}\n\n"
                "Answer (cite sources using [Source N] notation):"
            )
        return (
            f"Question: {question}\n\n"
            "No relevant context documents were found. "
            "State that you cannot answer without sufficient context."
        )

    def _fallback_answer(self, question: str, sources: List[dict]) -> str:
        """Return a text-only answer when LLM is unavailable."""
        if not sources:
            return (
                "No relevant documents found for your query. "
                "The legal knowledge base may be empty or the query may be too specific."
            )
        snippets = "\n\n".join(
            f"[Source {s['index']}] {s['title']}:\n{s['snippet']}"
            for s in sources
        )
        return (
            f"The following relevant documents were found (LLM synthesis unavailable):\n\n"
            f"{snippets}"
        )
