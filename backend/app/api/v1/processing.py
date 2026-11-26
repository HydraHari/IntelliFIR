"""
api/v1/processing.py — AI pipeline execution and extraction inspection endpoints.
"""
from __future__ import annotations

import logging
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.complaint import Complaint
from app.models.extraction import ExtractedEntity, ExtractedFact
from app.models.user import User
from app.schemas.extraction import (
    EntityResponse,
    EvidenceSpanResponse,
    ExtractionResultResponse,
    FactResponse,
)
from app.services.audit_service import create_audit_log
from app.services.extraction_service import process_complaint_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["Processing"])


@router.post("/{complaint_id}/process", response_model=ExtractionResultResponse)
def trigger_processing(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger the BERT NER and structured facts extraction pipeline on a complaint."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    structured_case = process_complaint_pipeline(db, complaint)

    create_audit_log(
        db=db,
        action="complaint_processed",
        resource_type="complaint",
        resource_id=str(complaint.id),
        user_id=current_user.id,
    )

    entities = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.complaint_id == complaint.id)
        .all()
    )
    facts = (
        db.query(ExtractedFact)
        .filter(ExtractedFact.complaint_id == complaint.id)
        .all()
    )

    return ExtractionResultResponse(
        complaint_id=complaint.id,
        entities=[EntityResponse.model_validate(e) for e in entities],
        facts=[FactResponse.model_validate(f) for f in facts],
        entity_count=len(entities),
        fact_count=len(facts),
    )


@router.get("/{complaint_id}/extraction", response_model=ExtractionResultResponse)
def get_extraction(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve all extracted entities, structured facts, and evidence spans for split-screen inspection."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    entities = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.complaint_id == complaint.id)
        .all()
    )
    facts = (
        db.query(ExtractedFact)
        .filter(ExtractedFact.complaint_id == complaint.id)
        .all()
    )

    return ExtractionResultResponse(
        complaint_id=complaint.id,
        entities=[EntityResponse.model_validate(e) for e in entities],
        facts=[FactResponse.model_validate(f) for f in facts],
        entity_count=len(entities),
        fact_count=len(facts),
    )
