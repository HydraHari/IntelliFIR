"""
models/extraction.py — ExtractedEntity, ExtractedFact, EvidenceSpan ORM models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExtractedEntity(Base):
    """Named entity extracted from complaint text via NER."""
    __tablename__ = "extracted_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_text: Mapped[str] = mapped_column(String(1024), nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # PERSON, LOCATION, DATE, TIME, ORG, OTHER
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    source_sentence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="bert-ner"
    )

    # Relationships
    complaint = relationship("Complaint", back_populates="entities")

    def __repr__(self) -> str:
        return (
            f"<ExtractedEntity type={self.entity_type} "
            f"text={self.entity_text[:30]!r}>"
        )


class ExtractedFact(Base):
    """Structured fact extracted from complaint text."""
    __tablename__ = "extracted_facts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fact_type: Mapped[str] = mapped_column(String(128), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    source_span_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_span_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_certain: Mapped[bool] = mapped_column(nullable=False, default=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    complaint = relationship("Complaint", back_populates="facts")
    evidence_spans = relationship(
        "EvidenceSpan",
        back_populates="fact",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ExtractedFact type={self.fact_type} value={self.fact_value[:30]!r}>"


class EvidenceSpan(Base):
    """Links a fact to a specific text span in the original complaint."""
    __tablename__ = "evidence_spans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_facts.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    source_sentence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="regex"
    )

    # Relationships
    fact = relationship("ExtractedFact", back_populates="evidence_spans")

    def __repr__(self) -> str:
        return f"<EvidenceSpan text={self.original_text[:30]!r}>"
