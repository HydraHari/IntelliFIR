"""
schemas/review.py — Review record schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewActionRequest(BaseModel):
    action: str = Field(
        pattern="^(opened|approved|rejected|edited|clarification_requested|finding_reviewed)$"
    )
    notes: Optional[str] = None


class ReviewRecordResponse(BaseModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    reviewer_id: uuid.UUID
    action: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: List[ReviewRecordResponse]
    total: int
