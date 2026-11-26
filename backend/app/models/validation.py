"""
models/validation.py — ValidationFinding ORM model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FindingCategory(str, enum.Enum):
    unsupported_claim = "unsupported_claim"
    missing_information = "missing_information"
    ambiguity = "ambiguity"
    contradiction = "contradiction"
    timeline_inconsistency = "timeline_inconsistency"
    uncertainty = "uncertainty"


class FindingSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ReviewerDecision(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    needs_clarification = "needs_clarification"


class ValidationFinding(Base):
    __tablename__ = "validation_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fir_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_id: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # human-readable e.g. VF-001
    category: Mapped[FindingCategory] = mapped_column(
        Enum(FindingCategory, name="finding_category"), nullable=False
    )
    draft_claim: Mapped[str] = mapped_column(Text, nullable=False)
    source_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity"), nullable=False
    )
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_decision: Mapped[ReviewerDecision] = mapped_column(
        Enum(ReviewerDecision, name="reviewer_decision"),
        nullable=False,
        default=ReviewerDecision.pending,
    )
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    # Relationships
    draft = relationship("FIRDraft", back_populates="validation_findings")
    reviewer = relationship("User", back_populates="validation_reviews")

    def __repr__(self) -> str:
        return (
            f"<ValidationFinding {self.finding_id} "
            f"category={self.category} severity={self.severity}>"
        )
