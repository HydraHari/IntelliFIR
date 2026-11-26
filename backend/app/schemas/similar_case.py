"""
schemas/similar_case.py — Similar case search schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SimilarCaseIngestRequest(BaseModel):
    reference_id: str = Field(min_length=1, max_length=128)
    summary: str = Field(min_length=10)
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SimilarCaseSearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SimilarCaseResult(BaseModel):
    id: uuid.UUID
    reference_id: str
    summary: str
    category: Optional[str]
    score: float
    metadata: Optional[Dict[str, Any]]


class SimilarCaseSearchResponse(BaseModel):
    query: str
    results: List[SimilarCaseResult]
    total_found: int


class SimilarCaseIngestResponse(BaseModel):
    id: uuid.UUID
    reference_id: str
    embedding_id: int
    message: str
