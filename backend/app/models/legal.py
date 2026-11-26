"""
models/legal.py — SimilarCase and LegalDocument ORM models.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SimilarCase(Base):
    """Historical case stored in the FAISS-backed similarity index."""
    __tablename__ = "similar_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True, unique=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    embedding_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # FAISS index position
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SimilarCase ref={self.reference_id} category={self.category}>"


class LegalDocument(Base):
    """Legal statute, section, or precedent stored for RAG retrieval."""
    __tablename__ = "legal_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provision_type: Mapped[str] = mapped_column(
        String(128), nullable=False, default="statute"
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    embedding_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<LegalDocument title={self.title[:50]!r} source={self.source}>"
