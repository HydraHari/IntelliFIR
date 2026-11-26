"""
app/main.py — FastAPI Application Entrypoint for IntelliFIR.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("intellifir")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown actions."""
    logger.info("Starting IntelliFIR backend v%s ...", settings.APP_VERSION)
    # Ensure all DB tables are created
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")
    except Exception as exc:
        logger.error("Database connection/migration failed: %s", exc)

    # If DEMO_MODE is true, seed demo data
    if settings.DEMO_MODE:
        logger.info("DEMO_MODE=true detected. Seeding fictional demo cases...")
        try:
            from app.core.demo_data import seed_demo_data
            seed_demo_data()
        except Exception as exc:
            logger.warning("Demo data seeding encountered: %s", exc)

    yield
    logger.info("Shutting down IntelliFIR backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "IntelliFIR — Evidence-Grounded AI Framework for Reliable FIR Draft Generation and Validation. "
        "Transforms citizen complaints into structured case representations, linked evidence spans, "
        "preliminary drafts, and independent factual validation reports."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_v1_router)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Health check endpoint for Docker container and orchestrator probes."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "demo_mode": settings.DEMO_MODE,
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to IntelliFIR API. Visit /docs for interactive Swagger documentation.",
        "tagline": "Turning citizen complaints into evidence-grounded FIR drafts.",
    }
