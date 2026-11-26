"""
api/v1/drafts.py — FIR Draft generation, inspection, editing, and document export.
"""
from __future__ import annotations

import logging
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.complaint import Complaint
from app.models.draft import FIRDraft
from app.models.user import User
from app.schemas.draft import (
    DraftClaimResponse,
    DraftGenerateRequest,
    DraftResponse,
    DraftUpdateRequest,
)
from app.services.audit_service import create_audit_log
from app.services.draft_service import export_draft_docx, export_draft_pdf, generate_fir_draft

logger = logging.getLogger(__name__)
router = APIRouter(tags=["FIR Drafts"])


@router.post("/complaints/{complaint_id}/generate-draft", response_model=DraftResponse)
def generate_draft(
    complaint_id: uuid.UUID,
    payload: DraftGenerateRequest = DraftGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a structured FIR draft using template or local LLM."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    draft = generate_fir_draft(
        db=db,
        complaint=complaint,
        user_id=current_user.id,
        method=payload.method,
    )

    create_audit_log(
        db=db,
        action="draft_generated",
        resource_type="draft",
        resource_id=str(draft.id),
        user_id=current_user.id,
        details={"method": payload.method, "version": draft.version},
    )

    return draft


@router.get("/complaints/{complaint_id}/draft", response_model=DraftResponse)
def get_complaint_draft(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the latest current FIR draft for a complaint."""
    draft = (
        db.query(FIRDraft)
        .filter(FIRDraft.complaint_id == complaint_id, FIRDraft.is_current == True)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No FIR draft generated for this complaint yet.",
        )
    return draft


@router.put("/drafts/{draft_id}", response_model=DraftResponse)
def update_draft(
    draft_id: uuid.UUID,
    payload: DraftUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Edit draft content during reviewer workflow."""
    draft = db.query(FIRDraft).filter(FIRDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FIR Draft not found.",
        )

    if payload.title is not None:
        draft.title = payload.title
    if payload.content is not None:
        draft.content = payload.content

    db.commit()
    db.refresh(draft)

    create_audit_log(
        db=db,
        action="draft_edited",
        resource_type="draft",
        resource_id=str(draft.id),
        user_id=current_user.id,
    )
    return draft


@router.get("/drafts/{draft_id}/export/docx")
def export_docx(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Export draft as Microsoft Word (.docx) document."""
    draft = db.query(FIRDraft).filter(FIRDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FIR Draft not found.",
        )

    buf = export_draft_docx(draft)
    filename = f"Draft_FIR_{draft.id.hex[:8]}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/drafts/{draft_id}/export/pdf")
def export_pdf(
    draft_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Export draft as official formatted PDF document with legal disclaimers."""
    draft = db.query(FIRDraft).filter(FIRDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FIR Draft not found.",
        )

    buf = export_draft_pdf(draft)
    filename = f"Draft_FIR_{draft.id.hex[:8]}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
