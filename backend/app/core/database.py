"""
core/database.py — SQLAlchemy engine, session factory, declarative base.
"""
from __future__ import annotations

import logging
from pathlib import Path
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.config import settings

logger = logging.getLogger("intellifir.database")

# Register SQLite compilation hooks for Postgres-specific types
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"

def _get_engine():
    # Attempt Postgres if driver available and reachable
    if settings.DATABASE_URL.startswith("postgres"):
        try:
            eng = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.DEBUG,
                connect_args={"connect_timeout": 2},
            )
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL successfully.")
            return eng
        except Exception as e:
            logger.warning(
                "PostgreSQL connection failed (%s). Falling back to persistent SQLite for local demonstration.",
                e,
            )

    # Persistent SQLite fallback for local demo
    base_dir = Path(__file__).resolve().parent.parent.parent
    sqlite_path = base_dir / "intellifir.db"
    sqlite_url = f"sqlite:///{sqlite_path}"
    logger.info("Using SQLite database at %s", sqlite_path)
    eng = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
    # Enable foreign key enforcement in SQLite
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng

engine = _get_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
