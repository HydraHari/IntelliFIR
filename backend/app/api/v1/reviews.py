"""
api/v1/reviews.py — Reviewer workflow tracking and audit records.
"""
from __future__ import annotations

import logging
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.complaint import ComplaintStatus
from app.models.draft import FIRDraft
from app.models.review import ReviewAction, ReviewRecord
from app.models.user import User
from app.schemas.review import (
    ReviewActionRequest,
    ReviewListResponse,
    ReviewRecordResponse,
)
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reviews"])


@router.post("/drafts/{draft_id}/review", response_model=ReviewRecordResponse, status_code=status.HTTP_201_CREATED)
def record_draft_review(
    draft_id: uuid.UUID,
    payload: ReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Record a reviewer action on a FIR draft (approve, reject, edit, request clarification)."""
    draft = db.query(FIRDraft).filter(FIRDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FIR Draft not found.",
        )

    # Permission check: reviewer or admin
    if current_user.role.value not in ["administrator", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authorized reviewers and administrators can perform draft reviews.",
        )

    action_enum = ReviewAction(payload.action)
    review_record = ReviewRecord(
        draft_id=draft.id,
        reviewer_id=current_user.id,
        action=action_enum,
        notes=payload.notes,
    )
    db.add(review_record)

    # Update complaint status accordingly
    complaint = draft.complaint
    if action_enum == ReviewAction.approved:
        complaint.status = ComplaintStatus.reviewed
    elif action_enum == ReviewAction.clarification_requested:
        complaint.status = ComplaintStatus.validation_required
    elif action_enum == ReviewAction.rejected:
        complaint.status = ComplaintStatus.under_review

    db.commit()
    db.refresh(review_record)

    create_audit_log(
        db=db,
        action=f"draft_review_{payload.action}",
        resource_type="draft",
        resource_id=str(draft.id),
        user_id=current_user.id,
        details={"action": payload.action, "notes": payload.notes},
    )

    return review_record


@router.get("/reviews", response_model=ReviewListResponse)
def list_review_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List recent review records across drafts."""
    query = db.query(ReviewRecord).order_by(ReviewRecord.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return ReviewListResponse(
        items=[ReviewRecordResponse.model_validate(r) for r in items],
        total=total,
    )
