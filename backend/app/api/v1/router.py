"""
api/v1/router.py — Master API v1 router registering all domain sub-routers.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.assistant import router as assistant_router
from app.api.v1.auth import router as auth_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.drafts import router as drafts_router
from app.api.v1.legal import router as legal_router
from app.api.v1.models import router as models_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.processing import router as processing_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.similar_cases import router as similar_cases_router
from app.api.v1.validation import router as validation_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(complaints_router)
api_v1_router.include_router(processing_router)
api_v1_router.include_router(drafts_router)
api_v1_router.include_router(validation_router)
api_v1_router.include_router(similar_cases_router)
api_v1_router.include_router(legal_router)
api_v1_router.include_router(assistant_router)
api_v1_router.include_router(reviews_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(evaluation_router)
