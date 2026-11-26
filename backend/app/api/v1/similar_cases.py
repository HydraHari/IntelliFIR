"""
api/v1/similar_cases.py — Semantic similar case retrieval via Sentence Transformers and FAISS.
"""
from __future__ import annotations

import logging
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.legal import SimilarCase
from app.models.user import User
from app.schemas.similar_case import (
    SimilarCaseIngestRequest,
    SimilarCaseIngestResponse,
    SimilarCaseResult,
    SimilarCaseSearchRequest,
    SimilarCaseSearchResponse,
)
from app.services.audit_service import create_audit_log
from app.services.similar_case_service import ingest_case, search_similar_cases

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/similar-cases", tags=["Similar Cases"])


@router.post("/search", response_model=SimilarCaseSearchResponse)
def search_cases(
    payload: SimilarCaseSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Semantic vector search for similar historical complaints and FIRs."""
    results = search_similar_cases(
        db=db,
        query_text=payload.query,
        top_k=payload.top_k,
        threshold=payload.threshold,
    )

    formatted_results = []
    for r in results:
        # Fetch DB record if present
        db_case = (
            db.query(SimilarCase)
            .filter(SimilarCase.reference_id == r["reference_id"])
            .first()
        )
        case_id = db_case.id if db_case else uuid.uuid4()
        formatted_results.append(
            SimilarCaseResult(
                id=case_id,
                reference_id=r["reference_id"],
                summary=r["summary"],
                category=r.get("category"),
                score=r["score"],
                metadata=db_case.metadata_ if db_case else {},
            )
        )

    return SimilarCaseSearchResponse(
        query=payload.query,
        results=formatted_results,
        total_found=len(formatted_results),
    )


@router.post("/ingest", response_model=SimilarCaseIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_similar_case(
    payload: SimilarCaseIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Ingest a historical case summary into FAISS index and database."""
    existing = db.query(SimilarCase).filter(SimilarCase.reference_id == payload.reference_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case with reference_id '{payload.reference_id}' already exists.",
        )

    case_obj = ingest_case(
        db=db,
        reference_id=payload.reference_id,
        summary=payload.summary,
        category=payload.category,
        metadata=payload.metadata,
    )

    create_audit_log(
        db=db,
        action="similar_case_ingested",
        resource_type="similar_case",
        resource_id=str(case_obj.id),
        user_id=current_user.id,
    )

    return SimilarCaseIngestResponse(
        id=case_obj.id,
        reference_id=case_obj.reference_id,
        embedding_id=case_obj.embedding_id or 0,
        message="Case indexed successfully in FAISS vector store.",
    )
