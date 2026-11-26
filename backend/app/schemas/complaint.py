"""
schemas/complaint.py — Complaint request/response schemas.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplaintCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=512)
    raw_text: str = Field(min_length=10)
    language: str = Field(default="en", max_length=16)
    incident_date: Optional[date] = None
    incident_location: Optional[str] = Field(default=None, max_length=512)


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    reference_id: str
    title: str
    language: str
    incident_date: Optional[date]
    incident_location: Optional[str]
    status: str
    submitted_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintDetailResponse(ComplaintResponse):
    raw_text: Optional[str]
    extracted_text: Optional[str]
    structured_data: Optional[Dict[str, Any]]


class ComplaintListResponse(BaseModel):
    items: List[ComplaintResponse]
    total: int
    skip: int
    limit: int


class ComplaintStatusUpdate(BaseModel):
    status: str
