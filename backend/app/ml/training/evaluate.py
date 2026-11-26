"""
ml/training/evaluate.py — Precision, Recall, F1 evaluation for Complaint NER models.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
from app.ml.training.dataset import ID_TO_LABEL, LABEL_LIST

logger = logging.getLogger(__name__)


def compute_ner_metrics(
    predictions: np.ndarray, labels: np.ndarray
) -> Dict[str, Any]:
    """
    Compute seqeval / entity-level precision, recall, and F1.
    Ignores padding and -100 labels.
    """
    preds = np.argmax(predictions, axis=2)

    true_predictions = [
        [ID_TO_LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(preds, labels)
    ]
    true_labels = [
        [ID_TO_LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(preds, labels)
    ]

    try:
        from seqeval.metrics import (
            classification_report,
            f1_score,
            precision_score,
            recall_score,
        )

        p = float(precision_score(true_labels, true_predictions))
        r = float(recall_score(true_labels, true_predictions))
        f1 = float(f1_score(true_labels, true_predictions))
        report = classification_report(true_labels, true_predictions, output_dict=True)

        return {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
            "detailed_report": report,
        }
    except ImportError:
        logger.warning("seqeval not installed; falling back to token-level accuracy")
        # Token-level fallback calculation
        flat_preds = [p for sub in true_predictions for p in sub]
        flat_labels = [l for sub in true_labels for l in sub]

        correct = sum(1 for p, l in zip(flat_preds, flat_labels) if p == l)
        total = max(len(flat_labels), 1)
        acc = correct / total

        return {
            "precision": round(acc, 4),
            "recall": round(acc, 4),
            "f1": round(acc, 4),
            "note": "Token-level accuracy (install seqeval for span-level entity metrics)",
        }


def evaluate_ner_checkpoint(
    model_checkpoint: str,
    test_data: List[Dict[str, Any]],
    device: str = "cpu",
) -> Dict[str, Any]:
    """
    Run evaluation on a test dataset for a given checkpoint (pretrained or fine-tuned).
    """
    from transformers import AutoModelForTokenClassification, AutoTokenizer
    from app.ml.training.dataset import ComplaintNERDataset

    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    model = AutoModelForTokenClassification.from_pretrained(model_checkpoint)
    model.to(device)
    model.eval()

    dataset = ComplaintNERDataset(test_data, tokenizer=tokenizer)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=8, shuffle=False)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits.detach().cpu().numpy()
            all_preds.append(logits)
            all_labels.append(labels.numpy())

    if not all_preds:
        return {"error": "No test samples provided for evaluation"}

    preds_concat = np.concatenate(all_preds, axis=0)
    labels_concat = np.concatenate(all_labels, axis=0)

    results = compute_ner_metrics(preds_concat, labels_concat)
    results["model_checkpoint"] = model_checkpoint
    results["num_samples"] = len(test_data)
    return results
