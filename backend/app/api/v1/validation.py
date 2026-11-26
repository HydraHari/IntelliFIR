"""
api/v1/validation.py — Independent factual validation and report review endpoints.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.draft import FIRDraft
from app.models.user import User
from app.models.validation import (
    FindingSeverity,
    ReviewerDecision,
    ValidationFinding,
)
from app.schemas.clarification import ClarificationResponse
from app.schemas.validation import (
    FindingDecisionUpdate,
    ValidationFindingResponse,
    ValidationResultResponse,
)
from app.services.audit_service import create_audit_log
from app.services.clarification_service import generate_clarification_questionnaire
from app.services.validation_service import validate_fir_draft

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Validation"])


@router.post("/drafts/{draft_id}/validate", response_model=ValidationResultResponse)
def trigger_validation(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Run independent factual validator against original complaint and return report."""
    draft = db.query(FIRDraft).filter(FIRDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FIR Draft not found.",
        )

    findings = validate_fir_draft(db, draft)

    create_audit_log(
        db=db,
        action="draft_validated",
        resource_type="draft",
        resource_id=str(draft.id),
        user_id=current_user.id,
        details={"finding_count": len(findings)},
    )

    return _build_validation_response(draft.id, findings)


@router.get("/drafts/{draft_id}/validation", response_model=ValidationResultResponse)
def get_validation_report(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve full validation report for a draft."""
    findings = (
        db.query(ValidationFinding)
        .filter(ValidationFinding.draft_id == draft_id)
        .all()
    )
    return _build_validation_response(draft_id, findings)


@router.get("/complaints/{complaint_id}/clarifications", response_model=ClarificationResponse)
def get_complaint_clarifications(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate structured investigative questions for missing elements, ambiguities, and gaps."""
    from app.models.complaint import Complaint
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Get latest findings if available
    draft = db.query(FIRDraft).filter(FIRDraft.complaint_id == complaint_id, FIRDraft.is_current == True).first()
    findings = []
    if draft:
        findings = db.query(ValidationFinding).filter(ValidationFinding.draft_id == draft.id).all()

    return generate_clarification_questionnaire(complaint, complaint.structured_data, findings)


@router.put("/findings/{finding_id}/decision", response_model=ValidationFindingResponse)
def update_finding_decision(
    finding_id: uuid.UUID,
    payload: FindingDecisionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Reviewer decision on a specific validation finding (accept, reject, needs_clarification)."""
    finding = db.query(ValidationFinding).filter(ValidationFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation finding not found.",
        )

    finding.reviewer_decision = ReviewerDecision(payload.reviewer_decision)
    finding.reviewer_notes = payload.reviewer_notes
    finding.reviewed_by_id = current_user.id
    finding.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(finding)

    create_audit_log(
        db=db,
        action="finding_decision_updated",
        resource_type="validation_finding",
        resource_id=str(finding.id),
        user_id=current_user.id,
        details={"decision": payload.reviewer_decision},
    )

    return finding


def _build_validation_response(
    draft_id: uuid.UUID, findings: list[ValidationFinding]
) -> ValidationResultResponse:
    high = sum(1 for f in findings if f.severity == FindingSeverity.high)
    med = sum(1 for f in findings if f.severity == FindingSeverity.medium)
    low = sum(1 for f in findings if f.severity == FindingSeverity.low)

    return ValidationResultResponse(
        draft_id=draft_id,
        total_findings=len(findings),
        high_severity=high,
        medium_severity=med,
        low_severity=low,
        findings=[ValidationFindingResponse.model_validate(f) for f in findings],
    )
