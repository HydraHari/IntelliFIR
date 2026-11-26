"""
ml/ner/preprocessing.py — Offset-preserving text preprocessing and language utilities.

Scope: English, Native Tamil script, and Tamil-English code-mixed complaints.
Note: Hindi is explicitly out of scope.

All character offsets (start_offset, end_offset) represent Python 3 Unicode code point
indices in the raw string buffer, strictly satisfying:
    0 <= start < end <= len(raw_text)
    raw_text[start : end] == span.text
Byte-level UTF-8 slicing is NOT used to prevent multi-byte decoding errors.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


def clean_text(text: str) -> str:
    """Normalize line endings and collapse duplicate blank lines for general reading."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def detect_language(text: str) -> Dict[str, Any]:
    """
    Detect language based on Unicode character script distribution.
    Supported Scope:
      - 'en': English (Latin)
      - 'ta': Native Tamil script (Unicode U+0B80–U+0BFF)
      - 'ta_en': Tamil-English code-mixed
    Excluded:
      - 'hi': Hindi / Devanagari (marked unsupported)
    """
    if not text or not text.strip():
        return {
            "language": "en",
            "supported": True,
            "confidence": 1.0,
            "is_multilingual": False,
            "script": "latin",
        }

    latin_count = len(re.findall(r"[a-zA-Z]", text))
    tamil_count = len(re.findall(r"[\u0B80-\u0BFF]", text))
    devanagari_count = len(re.findall(r"[\u0900-\u097F]", text))
    total_alpha = latin_count + tamil_count + devanagari_count

    if total_alpha == 0:
        return {
            "language": "en",
            "supported": True,
            "confidence": 1.0,
            "is_multilingual": False,
            "script": "latin",
        }

    # Explicit check for Hindi / Devanagari exclusion
    deva_ratio = devanagari_count / total_alpha
    if deva_ratio >= 0.20:
        return {
            "language": "hi",
            "supported": False,
            "confidence": round(deva_ratio, 3),
            "is_multilingual": False,
            "script": "devanagari",
            "error": "Hindi is excluded from the IntelliFIR research scope. Supported languages: English, Native Tamil, and Tamil-English code-mixed.",
        }

    latin_ratio = latin_count / total_alpha
    tamil_ratio = tamil_count / total_alpha

    distribution = {
        "en": round(latin_ratio, 3),
        "ta": round(tamil_ratio, 3),
    }

    # Tamil-English Code-mixed detection
    if latin_ratio >= 0.15 and tamil_ratio >= 0.15:
        return {
            "language": "ta_en",
            "supported": True,
            "dominant_language": "ta" if tamil_ratio > latin_ratio else "en",
            "confidence": round(latin_ratio + tamil_ratio, 3),
            "is_multilingual": True,
            "distribution": distribution,
        }

    if tamil_ratio > 0.40:
        return {
            "language": "ta",
            "supported": True,
            "confidence": round(tamil_ratio, 3),
            "is_multilingual": False,
            "script": "tamil",
            "distribution": distribution,
        }

    return {
        "language": "en",
        "supported": True,
        "confidence": round(latin_ratio, 3),
        "is_multilingual": False,
        "script": "latin",
        "distribution": distribution,
    }


def get_sentence_spans(raw_text: str) -> List[Tuple[str, int, int]]:
    """
    Segment raw_text into sentences while preserving exact Python character offsets.
    Each tuple is: (sentence_text, start_offset, end_offset)
    Guarantees: raw_text[start_offset:end_offset] == sentence_text
    Handles English, Native Tamil script, and punctuation.
    """
    if not raw_text:
        return []

    sentence_splitter = re.compile(r"([^.!?\n]+(?:[.!?]+|\n+|$))", re.MULTILINE)
    spans: List[Tuple[str, int, int]] = []

    for m in sentence_splitter.finditer(raw_text):
        raw_match = m.group(1)
        start = m.start(1)
        end = m.end(1)

        # Strip whitespace while adjusting offsets exactly
        stripped = raw_match.strip()
        if not stripped:
            continue

        l_strip = len(raw_match) - len(raw_match.lstrip())
        r_strip = len(raw_match) - len(raw_match.rstrip())

        adj_start = start + l_strip
        adj_end = end - r_strip
        sentence_text = raw_text[adj_start:adj_end]

        if sentence_text:
            spans.append((sentence_text, adj_start, adj_end))

    if not spans and raw_text.strip():
        stripped = raw_text.strip()
        l_strip = raw_text.find(stripped)
        spans.append((stripped, l_strip, l_strip + len(stripped)))

    return spans


def find_exact_span(
    raw_text: str,
    needle: str,
    preferred_start: int = 0,
    preferred_end: Optional[int] = None,
) -> Optional[Tuple[int, int]]:
    """
    Find exact needle in raw_text using Python character offsets.
    Returns (start, end) such that raw_text[start:end] == needle, or None.
    Works for English, native Tamil script, emojis, and punctuation.
    """
    if not needle or not raw_text:
        return None

    preferred_end = preferred_end if preferred_end is not None else len(raw_text)

    # 1. Search within the preferred window
    window = raw_text[preferred_start:preferred_end]
    idx = window.find(needle)
    if idx != -1:
        return (preferred_start + idx, preferred_start + idx + len(needle))

    # 2. Case-insensitive search within window (for Latin strings)
    idx = window.lower().find(needle.lower())
    if idx != -1:
        return (preferred_start + idx, preferred_start + idx + len(needle))

    # 3. Global search in raw_text
    idx = raw_text.find(needle)
    if idx != -1:
        return (idx, idx + len(needle))

    idx = raw_text.lower().find(needle.lower())
    if idx != -1:
        return (idx, idx + len(needle))

    return None


def split_into_sentences(text: str) -> List[str]:
    """Backwards-compatible sentence splitter returning sentence text strings."""
    spans = get_sentence_spans(text)
    return [s[0] for s in spans] if spans else [text.strip()]


# Legal Entity Type Normalization Mapping
_BERT_TO_INTELLIFIR: dict[str, str] = {
    "PER": "PERSON",
    "LOC": "LOCATION",
    "ORG": "ORGANIZATION",
    "DATE": "DATE",
    "TIME": "TIME",
    "MISC": "OTHER",
    "PERSON": "PERSON",
    "LOCATION": "LOCATION",
    "ORGANIZATION": "ORGANIZATION",
}


def normalize_entity_type(raw_type: str) -> str:
    """Map BERT NER labels to IntelliFIR entity types."""
    return _BERT_TO_INTELLIFIR.get(raw_type.upper(), "OTHER")
