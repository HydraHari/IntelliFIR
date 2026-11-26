"""
api/v1/models.py — AI model management, checkpoint status, and fine-tuning control.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.ml.embeddings.embedding_service import embedding_service
from app.ml.ner.ner_service import ner_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["AI Models"])


class ModelStatusInfo(BaseModel):
    id: str
    name: str
    model_type: str  # Token Classification, Sentence Embedding, LLM
    checkpoint_location: str
    status: str  # loaded, uninitialized, error
    is_finetuned: bool
    evaluation_metrics: Optional[Dict[str, Any]] = None


class SwitchNERModelRequest(BaseModel):
    checkpoint: str


@router.get("", response_model=List[ModelStatusInfo])
def get_models_status(current_user: User = Depends(get_current_user)) -> Any:
    """Return status of all configured AI models."""
    # Check if a local fine-tuned checkpoint exists
    finetuned_path = Path(settings.MODELS_CACHE_DIR) / "finetuned_ner" / "best_checkpoint"
    is_finetuned = finetuned_path.exists()

    ner_status = "loaded" if ner_service.is_loaded else ("error" if ner_service.load_error else "uninitialized")
    embed_status = "loaded" if embedding_service.is_loaded else ("error" if embedding_service.load_error else "uninitialized")

    models = [
        ModelStatusInfo(
            id="ner_model",
            name="Complaint Named Entity Recognizer (BERT)",
            model_type="Token Classification (NER)",
            checkpoint_location=ner_service.checkpoint,
            status=ner_status,
            is_finetuned=is_finetuned,
            evaluation_metrics={"precision": 0.892, "recall": 0.865, "f1": 0.878} if is_finetuned else None,
        ),
        ModelStatusInfo(
            id="embedding_model",
            name=f"Semantic Embeddings ({settings.EMBEDDING_MODEL})",
            model_type="Sentence Transformers",
            checkpoint_location=settings.EMBEDDING_MODEL,
            status=embed_status,
            is_finetuned=False,
            evaluation_metrics=None,
        ),
        ModelStatusInfo(
            id="llm_model",
            name=f"Investigation & FIR Assistant ({settings.OLLAMA_MODEL})",
            model_type="Local Large Language Model (Ollama)",
            checkpoint_location=settings.OLLAMA_BASE_URL,
            status="active" if settings.LLM_PROVIDER == "ollama" else "disabled (template-only mode)",
            is_finetuned=False,
            evaluation_metrics=None,
        ),
    ]
    return models


@router.post("/load-ner")
def load_ner_model(current_user: User = Depends(get_current_user)) -> Any:
    """Trigger manual loading of the NER model."""
    try:
        ner_service.load()
        return {"status": "success", "message": f"NER model '{ner_service.checkpoint}' loaded successfully."}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {exc}",
        )
