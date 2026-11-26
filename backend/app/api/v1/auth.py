"""
api/v1/auth.py — Authentication endpoints (register, login, me).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserRegisterRequest, UserResponse
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class JsonLoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> Any:
    """Register a new user."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    role_val = payload.role
    if role_val == "admin":
        role_val = "administrator"
    elif role_val == "officer":
        role_val = "investigator"

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole(role_val),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        action="user_registered",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """Login accepting either JSON {email, password} or OAuth2 form."""
    email_or_user = ""
    password = ""

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email_or_user = body.get("email") or body.get("username", "")
        password = body.get("password", "")
    else:
        form = await request.form()
        email_or_user = form.get("username") or form.get("email", "")
        password = form.get("password", "")

    if not email_or_user or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/username and password are required.",
        )

    user = db.query(User).filter(User.email == email_or_user).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value, "email": user.email},
    )

    create_audit_log(
        db=db,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieve details of currently authenticated user."""
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Logout endpoint."""
    return {"status": "success", "message": "Logged out successfully"}
