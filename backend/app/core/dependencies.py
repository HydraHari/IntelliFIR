"""
core/dependencies.py — FastAPI dependency injection helpers.
"""
from __future__ import annotations

import logging
from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Decode JWT, fetch user from DB.
    Raises HTTP 401 if token is invalid or user does not exist/is inactive.
    """
    # Import here to avoid circular imports
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    subject: Optional[str] = payload.get("sub")
    if subject is None:
        raise credentials_exception

    try:
        user_id = UUID(subject)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    """Alias that guarantees the user is active (already checked in get_current_user)."""
    return current_user


# ---------------------------------------------------------------------------
# Role guards
# ---------------------------------------------------------------------------

def require_role(*roles: str):
    """
    Factory that returns a dependency enforcing role membership.

    Usage::

        @router.delete("/{id}", dependencies=[Depends(require_role("administrator"))])
    """
    def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {list(roles)}",
            )
        return current_user

    return _check
