"""
evaluation/baselines/baseline_b.py — Baseline B: Pure template extraction generation without validation.
"""
from __future__ import annotations

from typing import Dict, Any


def run_baseline_b(complaint_text: str) -> str:
    """
    Template extraction baseline: fills template slots without evidence linking
    or contradiction/ambiguity detection.
    """
    return (
        f"FIR DRAFT (TEMPLATE)\n"
        f"Statement: {complaint_text}\n"
        f"Generated automatically from keywords."
    )
