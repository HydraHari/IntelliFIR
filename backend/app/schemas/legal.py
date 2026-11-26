"""
schemas/legal.py — Legal document and similar case schemas.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LegalDocumentCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=512)
    source: str = Field(min_length=1, max_length=256)
    version: Optional[str] = None
    publication_date: Optional[date] = None
    content: str = Field(min_length=10)
    provision_type: str = Field(default="statute", max_length=128)
    metadata: Optional[Dict[str, Any]] = None


class LegalDocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    version: Optional[str]
    provision_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LegalSearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)


class LegalSearchResult(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    provision_type: str
    snippet: str
    score: float
