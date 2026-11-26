"""
evaluation/metrics.py — Statistical metrics calculation for FIR evaluation.
Calculates entity precision/recall/F1, supported claim rates, and detection metrics.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple


def calculate_prf(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """Calculate Precision, Recall, and F1 score from raw counts."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def evaluate_entity_extraction(
    predicted_entities: List[Dict[str, Any]],
    gold_entities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate predicted entities against gold annotations.
    Matches with substring tolerance on entity text and compatible entity categories.
    """
    if not gold_entities and not predicted_entities:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

    matched_gold = set()
    matched_pred = set()

    for p_idx, pred in enumerate(predicted_entities):
        p_text = pred["entity_text"].strip().lower()
        p_type = pred["entity_type"].upper()

        for g_idx, gold in enumerate(gold_entities):
            if g_idx in matched_gold:
                continue
            g_text = gold["text"].strip().lower()
            g_type = gold["type"].upper()

            # Text match (exact or substring) and compatible type
            type_compat = (
                p_type == g_type
                or (p_type == "PERSON" and g_type in ["PERSON", "COMPLAINANT", "ACCUSED", "WITNESS"])
                or (p_type == "LOCATION" and g_type == "LOCATION")
                or (p_type in ["DATE", "TIME"] and g_type in ["DATE", "TIME"])
                or (p_type in ["OTHER", "ORGANIZATION"] and g_type in ["OTHER", "ORGANIZATION", "PROPERTY"])
            )

            if type_compat and (p_text in g_text or g_text in p_text):
                matched_gold.add(g_idx)
                matched_pred.add(p_idx)
                break

    tp = len(matched_gold)
    fp = len(predicted_entities) - len(matched_pred)
    fn = len(gold_entities) - len(matched_gold)

    return calculate_prf(tp, fp, fn)


def evaluate_claim_grounding(
    draft_claims: List[str],
    source_complaint: str,
) -> Dict[str, Any]:
    """
    Measure the proportion of draft claims that are directly supported by source text.
    Extracts substantive factual tokens (excluding template headers) and evaluates grounding.
    """
    complaint_lower = source_complaint.lower()
    supported = 0
    unsupported = 0

    header_pattern = re.compile(
        r"^(?:complainant|informant|date|time|place|location|suspect|accused|persons|witnesses|property|loss|evidence|statement|incident|narrative|occurrence|review)\s*[:—\-]\s*",
        re.IGNORECASE,
    )

    for claim in draft_claims:
        if not claim.strip():
            continue

        clean_claim = header_pattern.sub("", claim).strip()
        tokens = [
            w.lower()
            for w in re.findall(r"\w+", clean_claim)
            if len(w) > 2
            and w.lower()
            not in {
                "the", "this", "that", "with", "from", "into", "also", "under", "been",
                "have", "were", "reported", "draft", "section", "bns", "applicable",
                "requires", "investigation", "action", "items", "none", "unspecified"
            }
        ]

        if not tokens:
            continue

        found_count = sum(1 for w in tokens if w in complaint_lower)
        ratio = found_count / len(tokens)

        # Grounded if at least 50% of substantive factual tokens are present in complaint
        if ratio >= 0.50:
            supported += 1
        else:
            unsupported += 1

    total = max(supported + unsupported, 1)
    return {
        "total_claims": supported + unsupported,
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "supported_claim_rate": round(supported / total, 4),
        "unsupported_claim_rate": round(unsupported / total, 4),
    }


def evaluate_detection_task(
    predicted_flags: List[str],
    gold_flags: List[str],
) -> Dict[str, Any]:
    """
    Evaluate binary detection of missing facts, contradictions, or ambiguities
    for a single sample.
    Correctly distinguishes true negatives (TP=0, FP=0, FN=0) without distorting F1.
    """
    if not gold_flags and not predicted_flags:
        # True negative sample
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "is_true_negative": True,
        }
    if not gold_flags and predicted_flags:
        # False alarm: positive predicted on negative ground truth
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0,
            "fp": len(predicted_flags),
            "fn": 0,
            "is_true_negative": False,
        }
    if gold_flags and not predicted_flags:
        # Miss: positive ground truth, but nothing predicted
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "tp": 0,
            "fp": 0,
            "fn": len(gold_flags),
            "is_true_negative": False,
        }

    tp = 0
    matched_gold = set()

    for p in predicted_flags:
        p_lower = p.strip().lower()
        p_words = set(re.findall(r"\w+", p_lower))
        for g_idx, g in enumerate(gold_flags):
            if g_idx in matched_gold:
                continue
            g_lower = g.strip().lower()
            g_words = set(re.findall(r"\w+", g_lower))
            if p_words.intersection(g_words) or p_lower in g_lower or g_lower in p_lower:
                tp += 1
                matched_gold.add(g_idx)
                break

    fp = len(predicted_flags) - tp
    fn = len(gold_flags) - len(matched_gold)

    res = calculate_prf(tp, fp, fn)
    res["is_true_negative"] = False
    return res


def aggregate_dataset_detection_metrics(
    eval_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate dataset-wide Micro PRF and Macro PRF over positive instances.
    Solves the zero-division class imbalance distortion.
    """
    total_tp = sum(e.get("tp", 0) for e in eval_list)
    total_fp = sum(e.get("fp", 0) for e in eval_list)
    total_fn = sum(e.get("fn", 0) for e in eval_list)
    true_negatives = sum(1 for e in eval_list if e.get("is_true_negative", False))

    micro_res = calculate_prf(total_tp, total_fp, total_fn)

    # Positive-instance macro PRF
    pos_evals = [e for e in eval_list if not e.get("is_true_negative", False)]
    if pos_evals:
        macro_p = sum(e["precision"] for e in pos_evals) / len(pos_evals)
        macro_r = sum(e["recall"] for e in pos_evals) / len(pos_evals)
        macro_f1 = (2 * macro_p * macro_r / (macro_p + macro_r)) if (macro_p + macro_r) > 0 else 0.0
    else:
        macro_p = macro_r = macro_f1 = 0.0

    return {
        "micro_precision": micro_res["precision"],
        "micro_recall": micro_res["recall"],
        "micro_f1": micro_res["f1"],
        "macro_precision_pos": round(macro_p, 4),
        "macro_recall_pos": round(macro_r, 4),
        "macro_f1_pos": round(macro_f1, 4),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "true_negatives": true_negatives,
    }
