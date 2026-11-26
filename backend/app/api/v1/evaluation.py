"""
api/v1/evaluation.py — Research evaluation execution and results retrieval.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

def _get_dataset_file() -> Path:
    candidates = [
        Path("evaluation/sample_dataset.json"),
        Path(__file__).resolve().parent.parent.parent.parent / "evaluation" / "sample_dataset.json",
        Path(__file__).resolve().parent.parent.parent / "evaluation" / "sample_dataset.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

def _get_results_file() -> Path:
    return Path("evaluation_results.json")


@router.get("/results")
def get_evaluation_results(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve existing evaluation results report."""
    results_file = _get_results_file()
    if not results_file.exists():
        return {
            "status": "not_performed",
            "message": "Evaluation not yet performed. Click 'Run Evaluation' to evaluate all three systems.",
            "results": None,
        }

    try:
        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read evaluation results: {exc}",
        )


@router.post("/run")
def trigger_evaluation(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Execute evaluation comparing Baseline A, Baseline B, and IntelliFIR on held-out dataset."""
    from evaluation.run_evaluation import run_pipeline_evaluation

    dataset_file = _get_dataset_file()
    results_file = _get_results_file()

    if not dataset_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation dataset not found at evaluation/sample_dataset.json",
        )

    try:
        results = run_pipeline_evaluation(str(dataset_file), str(results_file))
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {exc}",
        )
