"""
models/user.py — User ORM model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    administrator = "administrator"
    reviewer = "reviewer"
    investigator = "investigator"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.investigator
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
    complaints = relationship("Complaint", back_populates="submitter", lazy="dynamic")
    drafts = relationship("FIRDraft", back_populates="created_by_user", lazy="dynamic")
    validation_reviews = relationship(
        "ValidationFinding", back_populates="reviewer", lazy="dynamic"
    )
    review_records = relationship(
        "ReviewRecord", back_populates="reviewer", lazy="dynamic"
    )
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
