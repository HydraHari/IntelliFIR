"""
api/v1/dashboard.py — Dashboard analytics and live operational statistics.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.audit import AuditLog
from app.models.complaint import Complaint, ComplaintStatus
from app.models.draft import FIRDraft
from app.models.user import User
from app.models.validation import ValidationFinding
from app.schemas.dashboard import DashboardStatsResponse, StatusCount

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve operational metrics, status distribution, and recent activity from database."""
    total_complaints = db.query(Complaint).count()
    total_drafts = db.query(FIRDraft).count()
    total_findings = db.query(ValidationFinding).count()

    # Complaints count by status
    status_counts = (
        db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .all()
    )
    status_list = [
        StatusCount(status=s.value if hasattr(s, "value") else str(s), count=cnt)
        for s, cnt in status_counts
    ]

    pending_reviews = (
        db.query(Complaint)
        .filter(Complaint.status.in_([ComplaintStatus.validation_required, ComplaintStatus.under_review]))
        .count()
    )

    # Recent activity from audit log
    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    activity_items = [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in recent_logs
    ]

    return DashboardStatsResponse(
        total_complaints=total_complaints,
        complaints_by_status=status_list,
        total_drafts=total_drafts,
        total_findings=total_findings,
        pending_reviews=pending_reviews,
        recent_activity=activity_items,
    )
