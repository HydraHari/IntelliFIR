"""
schemas/extraction.py — Extraction result schemas.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel


class EntityResponse(BaseModel):
    id: uuid.UUID
    entity_text: str
    entity_type: str
    start_offset: int
    end_offset: int
    source_sentence: Optional[str]
    confidence: Optional[float]
    extraction_method: str

    model_config = {"from_attributes": True}


class EvidenceSpanResponse(BaseModel):
    id: uuid.UUID
    original_text: str
    start_offset: int
    end_offset: int
    source_sentence: Optional[str]
    extraction_method: str

    model_config = {"from_attributes": True}


class FactResponse(BaseModel):
    id: uuid.UUID
    fact_type: str
    fact_value: str
    source_text: Optional[str]
    is_certain: bool
    confidence: Optional[float]
    evidence_spans: List[EvidenceSpanResponse] = []

    model_config = {"from_attributes": True}


class ExtractionResultResponse(BaseModel):
    complaint_id: uuid.UUID
    entities: List[EntityResponse]
    facts: List[FactResponse]
    entity_count: int
    fact_count: int
