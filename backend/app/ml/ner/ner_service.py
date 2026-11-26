"""
ml/ner/ner_service.py — BERT token-classification NER service.

Uses the HuggingFace transformers pipeline with configurable checkpoint.
The service is a singleton that lazy-loads the model on first use.
"""
from __future__ import annotations

import logging
import threading
from typing import List, Optional

from app.core.config import settings
from app.ml.ner.preprocessing import (
    clean_text,
    find_exact_span,
    get_sentence_spans,
    normalize_entity_type,
    split_into_sentences,
)

logger = logging.getLogger(__name__)

_LOAD_LOCK = threading.Lock()


class NERService:
    """
    Named Entity Recognition using a BERT token-classification pipeline.

    Supported entity types: PERSON, LOCATION, ORGANIZATION, DATE, TIME, OTHER.
    The underlying model is configurable via NER_MODEL_CHECKPOINT.
    """

    def __init__(self, checkpoint: str = settings.NER_MODEL_CHECKPOINT):
        self.checkpoint = checkpoint
        self._pipeline = None
        self._load_error: Optional[str] = None

    def load(self) -> None:
        """
        Load the NER pipeline. Thread-safe; called at startup or on first use.
        Raises RuntimeError if the model cannot be loaded.
        """
        with _LOAD_LOCK:
            if self._pipeline is not None:
                return
            if self._load_error is not None:
                raise RuntimeError(self._load_error)

            try:
                from transformers import pipeline as hf_pipeline

                logger.info("Loading NER model: %s", self.checkpoint)
                self._pipeline = hf_pipeline(
                    "token-classification",
                    model=self.checkpoint,
                    aggregation_strategy="simple",
                    device=-1,  # CPU; set to 0 for GPU
                )
                logger.info("NER model loaded successfully.")
            except Exception as exc:
                self._load_error = (
                    f"Failed to load NER model '{self.checkpoint}': {exc}"
                )
                logger.error(self._load_error)
                raise RuntimeError(self._load_error) from exc

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def extract_entities(self, text: str) -> List[dict]:
        """
        Run NER on the provided text while preserving exact character offsets.

        :param text: Raw complaint text.
        :returns: List of dicts with keys:
                  entity_text, entity_type, start, end, score, source_sentence
        :raises RuntimeError: If the model is not loaded.
        """
        if self._pipeline is None:
            self.load()

        sentence_spans = get_sentence_spans(text)
        results: List[dict] = []

        for sentence, s_start, s_end in sentence_spans:
            try:
                raw_entities = self._pipeline(sentence)
            except Exception as exc:
                logger.warning("NER inference failed on sentence '%s': %s", sentence[:30], exc)
                continue

            for ent in raw_entities:
                entity_type = normalize_entity_type(ent.get("entity_group", "MISC"))
                word = ent.get("word", "").strip()
                if not word:
                    continue

                # Compute sentence-relative offsets first
                e_start = s_start + ent.get("start", 0)
                e_end = s_start + ent.get("end", len(word))

                # Verify exact invariant against original text
                if e_end > len(text) or text[e_start:e_end] != word:
                    # Search within sentence span
                    refined = find_exact_span(text, word, s_start, s_end)
                    if refined:
                        e_start, e_end = refined
                    else:
                        refined_global = find_exact_span(text, word)
                        if refined_global:
                            e_start, e_end = refined_global

                results.append(
                    {
                        "entity_text": text[e_start:e_end] if e_end <= len(text) and e_start >= 0 else word,
                        "entity_type": entity_type,
                        "start": e_start,
                        "end": e_end,
                        "score": float(ent.get("score", 0.0)),
                        "source_sentence": sentence,
                    }
                )

        return results

    def extract_entities_batch(self, texts: List[str]) -> List[List[dict]]:
        """
        Run NER on a list of texts. Returns a list of entity lists.
        """
        return [self.extract_entities(text) for text in texts]


# Module-level singleton — shared across the app lifetime
ner_service = NERService()
