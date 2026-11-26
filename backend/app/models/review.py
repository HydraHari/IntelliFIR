"""
models/review.py — ReviewRecord ORM model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReviewAction(str, enum.Enum):
    opened = "opened"
    approved = "approved"
    rejected = "rejected"
    edited = "edited"
    clarification_requested = "clarification_requested"
    finding_reviewed = "finding_reviewed"


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fir_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[ReviewAction] = mapped_column(
        Enum(ReviewAction, name="review_action"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    # Relationships
    draft = relationship("FIRDraft", back_populates="review_records")
    reviewer = relationship("User", back_populates="review_records")

    def __repr__(self) -> str:
        return f"<ReviewRecord action={self.action} draft={self.draft_id}>"
