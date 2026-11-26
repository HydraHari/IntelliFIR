"""
api/v1/assistant.py — RAG-based Investigation Assistant endpoints.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.complaint import Complaint
from app.models.user import User
from app.services.assistant_service import query_investigation_assistant
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["Investigation Assistant"])


class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    complaint_id: Optional[uuid.UUID] = None


class CitationItem(BaseModel):
    index: int
    title: str
    source: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None


class AssistantQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    citations: List[str] = []
    is_retrieval_only: bool = False


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Ask an investigation-support question. Answers are grounded in retrieved case documents and legal provisions."""
    complaint_context = None
    if payload.complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if complaint:
            complaint_context = complaint.raw_text or complaint.extracted_text

    result = query_investigation_assistant(
        question=payload.question,
        complaint_context=complaint_context,
    )

    create_audit_log(
        db=db,
        action="assistant_queried",
        resource_type="rag_assistant",
        user_id=current_user.id,
        details={"question_length": len(payload.question)},
    )

    return AssistantQueryResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        citations=result.get("citations", []),
        is_retrieval_only=result.get("is_retrieval_only", False),
    )
