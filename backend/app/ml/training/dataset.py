"""
ml/training/dataset.py — BIO tagging and dataset preparation for Complaint NER fine-tuning.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

# Standard entity types for legal/police complaint NER
LABEL_LIST = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-LOCATION",
    "I-LOCATION",
    "B-ORGANIZATION",
    "I-ORGANIZATION",
    "B-DATE",
    "I-DATE",
    "B-TIME",
    "I-TIME",
    "B-OTHER",
    "I-OTHER",
]
LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}


class ComplaintNERDataset(Dataset):
    """
    PyTorch Dataset for fine-tuning BERT / IndicBERT token classification
    with BIO (Begin-Inside-Outside) tagging.
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        tokenizer: AutoTokenizer,
        max_length: int = 512,
        label_to_id: Dict[str, int] = LABEL_TO_ID,
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_to_id = label_to_id
        self.encoded_data = self._preprocess_and_align()

    def _preprocess_and_align(self) -> List[Dict[str, torch.Tensor]]:
        encoded_samples = []

        for item in self.data:
            tokens = item.get("tokens", [])
            ner_tags = item.get("ner_tags", [])

            if not tokens:
                # If raw text + spans provided instead of pre-tokenized tokens
                text = item.get("text", "")
                entities = item.get("entities", [])
                tokens, ner_tags = self._text_and_spans_to_bio(text, entities)

            # Tokenize using huggingface tokenizer with word-level alignment
            encoding = self.tokenizer(
                tokens,
                is_split_into_words=True,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )

            word_ids = encoding.word_ids(batch_index=0)
            labels = []
            previous_word_idx = None

            for word_idx in word_ids:
                if word_idx is None:
                    # Special tokens ([CLS], [SEP], [PAD]) get -100 so CrossEntropy ignores them
                    labels.append(-100)
                elif word_idx != previous_word_idx:
                    # First subtoken of a word
                    tag = ner_tags[word_idx] if word_idx < len(ner_tags) else "O"
                    labels.append(self.label_to_id.get(tag, self.label_to_id["O"]))
                else:
                    # Subsequent subtokens within the same word:
                    # Option 1: -100, Option 2: maintain I-tag if B-tag
                    tag = ner_tags[word_idx] if word_idx < len(ner_tags) else "O"
                    if tag.startswith("B-"):
                        tag = "I-" + tag[2:]
                    labels.append(self.label_to_id.get(tag, self.label_to_id["O"]))
                previous_word_idx = word_idx

            encoded_samples.append({
                "input_ids": encoding["input_ids"].squeeze(0),
                "attention_mask": encoding["attention_mask"].squeeze(0),
                "labels": torch.tensor(labels, dtype=torch.long),
            })

        return encoded_samples

    @staticmethod
    def _text_and_spans_to_bio(
        text: str, entities: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """
        Convert raw string text and character spans into token list and BIO tags.
        """
        # Simple whitespace/punctuation split
        import re
        token_matches = list(re.finditer(r"\S+", text))
        tokens = [m.group(0) for m in token_matches]
        bio_tags = ["O"] * len(tokens)

        for ent in entities:
            e_start = ent.get("start", 0)
            e_end = ent.get("end", 0)
            e_type = ent.get("type", "OTHER").upper()
            if e_type not in ["PERSON", "LOCATION", "ORGANIZATION", "DATE", "TIME", "OTHER"]:
                e_type = "OTHER"

            first = True
            for i, m in enumerate(token_matches):
                t_start = m.start()
                t_end = m.end()
                # Overlap check
                if t_start < e_end and t_end > e_start:
                    if first:
                        bio_tags[i] = f"B-{e_type}"
                        first = False
                    else:
                        bio_tags[i] = f"I-{e_type}"

        return tokens, bio_tags

    def __len__(self) -> int:
        return len(self.encoded_data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return self.encoded_data[idx]


def create_splits(
    data: List[Dict[str, Any]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split dataset into reproducible train, validation, and test splits."""
    import random
    rng = random.Random(seed)
    shuffled = list(data)
    rng.shuffle(shuffled)

    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train_data = shuffled[:train_end]
    val_data = shuffled[train_end:val_end]
    test_data = shuffled[val_end:]
    return train_data, val_data, test_data


def load_dataset_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON formatted complaint annotation data."""
    p = Path(file_path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
