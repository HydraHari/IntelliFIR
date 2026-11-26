"""
schemas/dashboard.py — Dashboard summary schemas.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardStatsResponse(BaseModel):
    total_complaints: int
    complaints_by_status: List[StatusCount]
    total_drafts: int
    total_findings: int
    pending_reviews: int
    recent_activity: List[Dict[str, Any]]
