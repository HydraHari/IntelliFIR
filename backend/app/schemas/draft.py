"""
schemas/draft.py — FIR draft request/response schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DraftGenerateRequest(BaseModel):
    method: str = Field(
        default="template",
        pattern="^(template|llm|hybrid)$",
        description="Generation method",
    )


class DraftUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=512)
    content: Optional[str] = Field(default=None, min_length=10)


class DraftClaimResponse(BaseModel):
    id: uuid.UUID
    claim_text: str
    claim_type: str
    is_supported: Optional[bool]

    model_config = {"from_attributes": True}


class DraftResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    version: int
    title: str
    content: str
    generation_method: str
    is_current: bool
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    structured_draft: Optional[Dict[str, Any]]
    claims: List[DraftClaimResponse] = []

    model_config = {"from_attributes": True}
