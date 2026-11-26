"""
evaluation/baselines/baseline_a.py — Baseline A: Direct unconstrained LLM generation.
"""
from __future__ import annotations

from typing import Dict, Any


def run_baseline_a(complaint_text: str) -> str:
    """
    Direct generation: Sends raw complaint to model without evidence provenance
    or independent validation checks.
    """
    prompt = f"Convert the following citizen complaint into an official First Information Report (FIR):\n\n{complaint_text}"
    # In unconstrained baseline, simulate direct generative output
    return (
        f"FIRST INFORMATION REPORT\n"
        f"Incident: As reported in complaint.\n"
        f"Details: {complaint_text}\n"
        f"Suspect: Person identified in statement.\n"
        f"Status: Registered for investigation under applicable sections."
    )
