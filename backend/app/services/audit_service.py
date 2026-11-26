"""
services/audit_service.py — Audit logging service for user and system actions.
Ensures sensitive complaint content is never written into audit logs.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Record an action in the audit log.
    Sanitizes details so raw complaint text or sensitive PII is never stored.
    """
    safe_details = {}
    if details:
        # Filter out potential raw text fields
        for k, v in details.items():
            if k in ["raw_text", "extracted_text", "password", "token", "content"]:
                safe_details[k] = "[REDACTED]"
            else:
                safe_details[k] = v

    log_entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        details=safe_details,
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
