"""
ml/training/trainer.py — Fine-tuning script for BERT / IndicBERT on Complaint NER.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from app.ml.training.dataset import (
    ComplaintNERDataset,
    LABEL_LIST,
    LABEL_TO_ID,
    ID_TO_LABEL,
    create_splits,
    load_dataset_from_json,
)
from app.ml.training.evaluate import compute_ner_metrics

logger = logging.getLogger(__name__)


def compute_metrics_for_trainer(eval_pred):
    predictions, labels = eval_pred
    return compute_ner_metrics(predictions, labels)


def train_complaint_ner(
    data_path: str,
    output_dir: str,
    model_checkpoint: str = "dslim/bert-base-NER",
    num_train_epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 3e-5,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Fine-tune a pretrained BERT / IndicBERT model for token classification on complaints.
    """
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    data = load_dataset_from_json(data_path)
    if not data:
        raise ValueError(f"No labeled data found at {data_path}. Training requires annotated data.")

    train_data, val_data, test_data = create_splits(data, seed=seed)
    logger.info(
        "Dataset splits: %d train, %d validation, %d test samples",
        len(train_data),
        len(val_data),
        len(test_data),
    )

    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    model = AutoModelForTokenClassification.from_pretrained(
        model_checkpoint,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
        ignore_mismatched_sizes=True,
    )

    train_dataset = ComplaintNERDataset(train_data, tokenizer=tokenizer)
    val_dataset = ComplaintNERDataset(val_data, tokenizer=tokenizer)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(out_path),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_train_epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=str(out_path / "logs"),
        logging_steps=10,
        save_total_limit=2,
        seed=seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics_for_trainer,
    )

    logger.info("Starting fine-tuning...")
    train_result = trainer.train()

    # Save final best model and tokenizer
    trainer.save_model(str(out_path / "best_checkpoint"))
    tokenizer.save_pretrained(str(out_path / "best_checkpoint"))

    # Evaluate on val set
    eval_metrics = trainer.evaluate()
    logger.info("Evaluation metrics: %s", eval_metrics)

    return {
        "status": "success",
        "output_dir": str(out_path / "best_checkpoint"),
        "train_loss": train_result.training_loss,
        "eval_metrics": eval_metrics,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune BERT on Complaint NER")
    parser.add_argument("--data-path", required=True, help="Path to labeled JSON dataset")
    parser.add_argument("--output-dir", default="./models_cache/finetuned_ner", help="Output directory")
    parser.add_argument("--model-checkpoint", default="dslim/bert-base-NER", help="Base model checkpoint")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    res = train_complaint_ner(
        data_path=args.data_path,
        output_dir=args.output_dir,
        model_checkpoint=args.model_checkpoint,
        num_train_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )
    print("Fine-tuning completed:", res)
