"""
api/v1/complaints.py — Ingestion, upload, listing, and retrieval of complaints.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.document import UploadedDocument
from app.models.user import User
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintDetailResponse,
    ComplaintListResponse,
    ComplaintResponse,
)
from app.services.audit_service import create_audit_log
from app.services.document_service import extract_text_from_file
from app.services.extraction_service import process_complaint_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _generate_ref_id() -> str:
    """Generate unique human-readable complaint reference ID."""
    rnd = uuid.uuid4().hex[:6].upper()
    return f"CMP-{rnd}"


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint_manual(
    payload: ComplaintCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Manually create a new complaint from plain text."""
    ref_id = _generate_ref_id()

    complaint = Complaint(
        reference_id=ref_id,
        title=payload.title,
        raw_text=payload.raw_text,
        extracted_text=payload.raw_text,
        language=payload.language,
        incident_date=payload.incident_date,
        incident_location=payload.incident_location,
        status=ComplaintStatus.processing,
        submitted_by_id=current_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    create_audit_log(
        db=db,
        action="complaint_created_manual",
        resource_type="complaint",
        resource_id=str(complaint.id),
        user_id=current_user.id,
    )

    # Process extraction in background task
    def _run_bg():
        from app.core.database import SessionLocal
        bg_db = SessionLocal()
        try:
            bg_c = bg_db.query(Complaint).get(complaint.id)
            if bg_c:
                process_complaint_pipeline(bg_db, bg_c)
        finally:
            bg_db.close()

    background_tasks.add_task(_run_bg)

    return complaint


@router.post("/upload", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def upload_complaint_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    language: str = Form("en"),
    incident_date: Optional[str] = Form(None),
    incident_location: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload a complaint document (PDF, DOCX, TXT, or Image/Scanned Doc).
    Validates file size, extracts text using PyMuPDF / docx / OCR, and processes pipeline.
    """
    # 1. Validate file size and type
    content_bytes = await file.read()
    file_size = len(content_bytes)

    if file_size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # 2. Save file securely with UUID stored_filename
    ext = Path(file.filename or "").suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = Path(settings.UPLOAD_DIR) / stored_name

    with open(dest_path, "wb") as f_out:
        f_out.write(content_bytes)

    # 3. Extract text
    mime = file.content_type or "application/octet-stream"
    try:
        extracted_text, ocr_used, meta = extract_text_from_file(str(dest_path), mime)
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from document: {exc}",
        )

    if not extracted_text:
        extracted_text = "[No readable text could be extracted from this document]"

    # 4. Parse date if provided
    parsed_date = None
    if incident_date:
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(incident_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    ref_id = _generate_ref_id()
    complaint = Complaint(
        reference_id=ref_id,
        title=title,
        raw_text=extracted_text,
        extracted_text=extracted_text,
        language=language,
        incident_date=parsed_date,
        incident_location=incident_location,
        status=ComplaintStatus.processing,
        submitted_by_id=current_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Record uploaded document
    doc_record = UploadedDocument(
        complaint_id=complaint.id,
        original_filename=file.filename or "unknown",
        stored_filename=stored_name,
        file_path=str(dest_path),
        file_type=ext.replace(".", ""),
        file_size=file_size,
        extracted_text=extracted_text,
        ocr_used=ocr_used,
    )
    db.add(doc_record)
    db.commit()

    create_audit_log(
        db=db,
        action="complaint_uploaded",
        resource_type="complaint",
        resource_id=str(complaint.id),
        user_id=current_user.id,
    )

    # Background processing
    def _run_bg():
        from app.core.database import SessionLocal
        bg_db = SessionLocal()
        try:
            bg_c = bg_db.query(Complaint).get(complaint.id)
            if bg_c:
                process_complaint_pipeline(bg_db, bg_c)
        finally:
            bg_db.close()

    background_tasks.add_task(_run_bg)

    return complaint


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List complaints with filtering and pagination."""
    query = db.query(Complaint)

    if status_filter:
        try:
            s_enum = ComplaintStatus(status_filter)
            query = query.filter(Complaint.status == s_enum)
        except ValueError:
            pass

    if search:
        s_term = f"%{search}%"
        query = query.filter(
            or_(
                Complaint.title.ilike(s_term),
                Complaint.reference_id.ilike(s_term),
                Complaint.incident_location.ilike(s_term),
            )
        )

    total = query.count()
    items = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    return ComplaintListResponse(
        items=[ComplaintResponse.model_validate(c) for c in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
def get_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve full details of a specific complaint."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )
    return ComplaintDetailResponse.model_validate(complaint)


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a complaint (authorized reviewers or administrators only)."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    # Permission check
    if current_user.role.value != "administrator" and complaint.submitted_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this complaint.",
        )

    create_audit_log(
        db=db,
        action="complaint_deleted",
        resource_type="complaint",
        resource_id=str(complaint_id),
        user_id=current_user.id,
    )

    db.delete(complaint)
    db.commit()
