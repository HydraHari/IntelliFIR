"""
api/v1/legal.py — Verified legal documents and statutory provisions retrieval.
"""
from __future__ import annotations

import logging
from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.legal import LegalDocument
from app.models.user import User
from app.schemas.legal import (
    LegalDocumentCreateRequest,
    LegalDocumentResponse,
    LegalSearchRequest,
    LegalSearchResult,
)
from app.services.audit_service import create_audit_log
from app.services.legal_service import add_legal_document, search_legal_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legal", tags=["Legal Retrieval"])


@router.post("/search", response_model=List[LegalSearchResult])
def search_legal(
    payload: LegalSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Semantic search over verified statutes, penal codes, and judicial precedents."""
    results = search_legal_documents(
        db=db,
        query=payload.query,
        top_k=payload.top_k,
    )

    formatted = []
    for r in results:
        db_doc = db.query(LegalDocument).filter(LegalDocument.title == r["title"]).first()
        doc_id = db_doc.id if db_doc else uuid.uuid4()
        formatted.append(
            LegalSearchResult(
                id=doc_id,
                title=r["title"],
                source=r["source"],
                provision_type=r["provision_type"],
                snippet=r["content"][:300] + ("..." if len(r["content"]) > 300 else ""),
                score=r["score"],
            )
        )
    return formatted


@router.post("/documents", response_model=LegalDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_legal_document(
    payload: LegalDocumentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Ingest a verified statutory document into the legal knowledgebase (admin/reviewer)."""
    if current_user.role.value not in ["administrator", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and authorized reviewers can add legal documents.",
        )

    doc = add_legal_document(
        db=db,
        title=payload.title,
        source=payload.source,
        content=payload.content,
        provision_type=payload.provision_type,
        version=payload.version,
        publication_date=payload.publication_date,
        metadata=payload.metadata,
    )

    create_audit_log(
        db=db,
        action="legal_document_added",
        resource_type="legal_document",
        resource_id=str(doc.id),
        user_id=current_user.id,
    )
    return doc


@router.get("/documents", response_model=List[LegalDocumentResponse])
def list_legal_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all verified legal documents."""
    docs = db.query(LegalDocument).order_by(LegalDocument.title.asc()).offset(skip).limit(limit).all()
    return docs
