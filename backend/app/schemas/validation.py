"""
schemas/validation.py — Validation finding schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ValidationFindingResponse(BaseModel):
    id: uuid.UUID
    finding_id: str
    category: str
    draft_claim: str
    source_evidence: Optional[str]
    explanation: str
    severity: str
    suggested_action: str
    reviewer_decision: str
    reviewer_notes: Optional[str]
    reviewed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ValidationResultResponse(BaseModel):
    draft_id: uuid.UUID
    total_findings: int
    high_severity: int
    medium_severity: int
    low_severity: int
    findings: List[ValidationFindingResponse]


class FindingDecisionUpdate(BaseModel):
    reviewer_decision: str = Field(
        pattern="^(accepted|rejected|needs_clarification)$"
    )
    reviewer_notes: Optional[str] = None
