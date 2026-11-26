"""
models/draft.py — FIRDraft and DraftClaim ORM models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FIRDraft(Base):
    """A generated FIR draft for a complaint."""
    __tablename__ = "fir_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_draft: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    generation_method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="template"
    )  # "template", "llm", "hybrid"
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    complaint = relationship("Complaint", back_populates="drafts")
    created_by_user = relationship("User", back_populates="drafts")
    claims = relationship(
        "DraftClaim", back_populates="draft", cascade="all, delete-orphan"
    )
    validation_findings = relationship(
        "ValidationFinding", back_populates="draft", cascade="all, delete-orphan"
    )
    review_records = relationship(
        "ReviewRecord", back_populates="draft", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<FIRDraft id={self.id} complaint={self.complaint_id} "
            f"v={self.version} method={self.generation_method}>"
        )


class DraftClaim(Base):
    """A single verifiable claim within a FIR draft."""
    __tablename__ = "draft_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fir_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence_span_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_spans.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_supported: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Relationships
    draft = relationship("FIRDraft", back_populates="claims")

    def __repr__(self) -> str:
        return f"<DraftClaim type={self.claim_type} supported={self.is_supported}>"
