"""
tests/test_preprocessing_and_provenance.py — Tests for offset-preserving text segmentation and language detection.
"""
import pytest
from app.ml.ner.preprocessing import (
    clean_text,
    detect_language,
    find_exact_span,
    get_sentence_spans,
    split_into_sentences,
)


def test_language_detection_english():
    text = "My name is Rajesh Sharma and my laptop was stolen from Sector 15."
    res = detect_language(text)
    assert res["language"] == "en"
    assert res["confidence"] > 0.8
    assert res["is_multilingual"] is False


def test_language_detection_hindi_out_of_scope():
    text = "मेरा नाम रमेश गुप्ता है और मेरी मोटरसाइकिल चोरी हो गई है।"
    res = detect_language(text)
    assert res["language"] == "hi"
    assert res["supported"] is False
    assert "error" in res


def test_language_detection_tamil():
    text = "என் பெயர் முருகன். சென்னை பேருந்து நிலையத்தில் எனது நகை திருடப்பட்டது."
    res = detect_language(text)
    assert res["language"] == "ta"
    assert res["confidence"] > 0.5


def test_language_detection_code_mixed():
    text = "My name is Ramesh. எனது பைக் திருடப்பட்டது near Gandhi Market."
    res = detect_language(text)
    assert res["language"] == "ta_en"
    assert res["is_multilingual"] is True
    assert "distribution" in res


def test_sentence_spans_strict_invariant():
    raw_text = (
        "I, Ramesh Gupta, report theft. On 12/08/2026 at 8:30 PM, my laptop was stolen.\n\n"
        "The balcony latch was broken. Please register an FIR."
    )
    spans = get_sentence_spans(raw_text)
    assert len(spans) >= 3

    for sentence_text, start, end in spans:
        # Strict mathematical invariant: raw_text[start:end] must equal sentence_text exactly
        assert raw_text[start:end] == sentence_text, f"Offset mismatch: '{raw_text[start:end]}' != '{sentence_text}'"
        assert len(sentence_text.strip()) > 0


def test_find_exact_span():
    raw_text = "The suspect Mohit Yadav arrived at 5:00 PM and demanded Rs. 50,000 cash."
    needle = "Mohit Yadav"
    span = find_exact_span(raw_text, needle)
    assert span is not None
    start, end = span
    assert raw_text[start:end] == needle

    needle_amt = "Rs. 50,000"
    span_amt = find_exact_span(raw_text, needle_amt)
    assert span_amt is not None
    assert raw_text[span_amt[0]:span_amt[1]] == needle_amt
