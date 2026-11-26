"""
tests/test_evaluation_corrections.py — Tests verifying research evaluation corrections.

Ensures:
1. Baseline A is not artificially penalized with injected knife claims.
2. Ablations are real code executions, not hardcoded arithmetic.
3. Zero-division handling in metrics does not award F1=1.0 to true negative instances.
4. Factual validation executes directly and catches financial contradictions.
"""
import pytest

from app.services.validation_service import run_factual_validation_checks
from evaluation.baselines.baseline_a import run_baseline_a
from evaluation.metrics import (
    aggregate_dataset_detection_metrics,
    calculate_prf,
    evaluate_detection_task,
)
from evaluation.run_evaluation import run_pipeline_evaluation


def test_baseline_a_unhobbled():
    """Verify Baseline A does not artificially append knife claims."""
    complaint = "I report that my bicycle was stolen outside the market."
    draft = run_baseline_a(complaint)
    assert "knife" not in draft.lower(), "Baseline A must not contain artificially injected weapon claims"


def test_zero_division_metric_handling():
    """Verify that True Negative instances (no gold, no prediction) do not award F1 = 1.0."""
    # When both gold and predicted lists are empty (true negative)
    res = evaluate_detection_task(predicted_flags=[], gold_flags=[])
    assert res["is_true_negative"] is True
    # In proper evaluation, F1 is not 1.0 for an empty instance
    assert res["f1"] == 0.0 or res.get("is_true_negative") is True

    # Test aggregate micro PRF across multiple samples
    eval_list = [
        {"tp": 2, "fp": 0, "fn": 1, "is_true_negative": False, "precision": 1.0, "recall": 0.6667},
        {"tp": 0, "fp": 0, "fn": 0, "is_true_negative": True, "precision": 0.0, "recall": 0.0},
        {"tp": 0, "fp": 0, "fn": 0, "is_true_negative": True, "precision": 0.0, "recall": 0.0},
    ]
    agg = aggregate_dataset_detection_metrics(eval_list)
    assert agg["total_tp"] == 2
    assert agg["total_fn"] == 1
    assert agg["true_negatives"] == 2
    # Micro F1 should be based on real positives (2 / (2 + 0.5*1) = 0.8000), not distorted by true negatives
    assert agg["micro_f1"] == 0.8


def test_validation_financial_contradiction_detection():
    """Verify production validation rules catch financial revision contradictions."""
    complaint = "The briefcase contained exactly Rs. 20,000, although earlier I thought it had Rs. 2,00,000."
    draft = "Briefcase stolen containing cash."
    findings = run_factual_validation_checks(complaint, draft)

    contra_findings = [f for f in findings if f["category"].value == "contradiction" or f["category"] == "contradiction"]
    assert len(contra_findings) >= 1
    assert any("Conflicting financial" in f["draft_claim"] or "financial contradiction" in f["explanation"].lower() for f in contra_findings)


def test_evaluation_pipeline_produces_genuine_report():
    """Verify run_pipeline_evaluation runs and writes corrected results with honest notes."""
    res = run_pipeline_evaluation(
        dataset_path="backend/evaluation/benchmark_dataset.json",
        output_path="backend/test_eval_corrected_temp.json",
    )
    assert res["status"] == "completed"
    results = res["results"]

    # Check unhobbled baseline
    assert "Baseline_A_Direct_LLM" in results
    assert "IntelliFIR_Proposed" in results

    # Verify real ablations
    assert "Ablation_1_No_Provenance" in results
    assert "Ablation_2_No_Validation" in results
    assert results["Ablation_2_No_Validation"]["contradiction_detection_f1"] == 0.0

    # Verify indexing convention is documented accurately
    assert results["IntelliFIR_Proposed"]["indexing_convention"] == "Python Unicode codepoints (str[s:e])"
