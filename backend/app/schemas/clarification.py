"""
schemas/clarification.py — Clarification question and investigative prompt schemas.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from pydantic import BaseModel


class ClarificationQuestion(BaseModel):
    id: str
    category: str
    priority: str  # "CRITICAL", "HIGH", "MEDIUM"
    target_entity: str
    prompt_question: str
    legal_rationale: str
    suggested_police_action: str


class ClarificationResponse(BaseModel):
    complaint_id: uuid.UUID
    reference_id: str
    total_questions: int
    critical_count: int
    questions: List[ClarificationQuestion]
