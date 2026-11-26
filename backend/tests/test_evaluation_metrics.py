"""
tests/test_evaluation_metrics.py — Tests for statistical evaluation formulas and benchmark dataset integrity.
"""
import json
from pathlib import Path
import pytest

from evaluation.metrics import (
    calculate_prf,
    evaluate_claim_grounding,
    evaluate_detection_task,
    evaluate_entity_extraction,
)
from evaluation.run_evaluation import run_pipeline_evaluation


def test_calculate_prf_perfect():
    res = calculate_prf(tp=10, fp=0, fn=0)
    assert res["precision"] == 1.0
    assert res["recall"] == 1.0
    assert res["f1"] == 1.0


def test_calculate_prf_zero():
    res = calculate_prf(tp=0, fp=5, fn=5)
    assert res["precision"] == 0.0
    assert res["recall"] == 0.0
    assert res["f1"] == 0.0


def test_evaluate_claim_grounding():
    complaint = "I, Ramesh Gupta, report that my laptop was stolen from Sector 15 on 12/08/2026."
    grounded_claims = [
        "Complainant: Ramesh Gupta",
        "Occurrence: stolen from Sector 15",
    ]
    ungrounded_claims = [
        "The accused was armed with a high caliber assault rifle.",
        "Loss incurred exceeds five million dollars.",
    ]

    res_grounded = evaluate_claim_grounding(grounded_claims, complaint)
    assert res_grounded["supported_claim_rate"] == 1.0
    assert res_grounded["unsupported_claim_rate"] == 0.0

    res_ungrounded = evaluate_claim_grounding(ungrounded_claims, complaint)
    assert res_ungrounded["supported_claim_rate"] == 0.0
    assert res_ungrounded["unsupported_claim_rate"] == 1.0


def test_benchmark_dataset_integrity():
    bench_path = Path("backend/evaluation/benchmark_dataset.json")
    if not bench_path.exists():
        bench_path = Path("evaluation/benchmark_dataset.json")
    assert bench_path.exists(), "Benchmark dataset file must exist"

    with open(bench_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    assert len(samples) >= 20, "Benchmark dataset must contain at least 20 diverse cases"
    for sample in samples:
        assert "id" in sample
        assert "text" in sample
        assert "gold_entities" in sample
        assert len(sample["text"]) > 20


def test_run_pipeline_evaluation_execution():
    bench_path = "backend/evaluation/benchmark_dataset.json"
    res = run_pipeline_evaluation(bench_path, output_path="backend/test_eval_output.json")
    assert res["status"] == "completed"
    assert "results" in res
    assert "IntelliFIR_Proposed" in res["results"]
    assert res["results"]["IntelliFIR_Proposed"]["provenance_invariant_pass_rate"] == 1.0
