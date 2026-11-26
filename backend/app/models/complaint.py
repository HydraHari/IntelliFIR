"""
models/complaint.py — Complaint ORM model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ComplaintStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    draft_generated = "draft_generated"
    validation_required = "validation_required"
    under_review = "under_review"
    reviewed = "reviewed"
    archived = "archived"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    incident_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    incident_location: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status"),
        nullable=False,
        default=ComplaintStatus.uploaded,
        index=True,
    )
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
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
    submitter = relationship("User", back_populates="complaints")
    documents = relationship(
        "UploadedDocument", back_populates="complaint", cascade="all, delete-orphan"
    )
    entities = relationship(
        "ExtractedEntity", back_populates="complaint", cascade="all, delete-orphan"
    )
    facts = relationship(
        "ExtractedFact", back_populates="complaint", cascade="all, delete-orphan"
    )
    drafts = relationship(
        "FIRDraft", back_populates="complaint", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Complaint id={self.id} ref={self.reference_id} status={self.status}>"
