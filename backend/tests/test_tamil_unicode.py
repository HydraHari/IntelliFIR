"""
tests/test_tamil_unicode.py — Tests for Native Tamil, Tamil-English code-mixed, and Unicode codepoint handling.

Verifies:
1. Native Tamil script detection and Hindi out-of-scope exclusion.
2. Exact character offset invariant: raw_text[start:end] == span_text for Tamil Unicode codepoints.
3. Information extraction on native Tamil complaints.
4. Handling of Tamil-English code-mixed text.
"""
import pytest

from app.ml.ner.preprocessing import (
    detect_language,
    find_exact_span,
    get_sentence_spans,
)
from app.services.extraction_service import (
    _extract_structured_facts,
    _rule_based_entity_fallback,
)


def test_language_detection_scope():
    """Verify supported scope: English, Native Tamil, Tamil-English code-mixed; Exclude Hindi."""
    # 1. English
    en_res = detect_language("I report that my mobile phone was snatched on 12/08/2026.")
    assert en_res["language"] == "en"
    assert en_res["supported"] is True

    # 2. Native Tamil Script
    ta_res = detect_language("என் பெயர் முருகன். சென்னை பேருந்து நிலையத்தில் எனது நகை திருடப்பட்டது.")
    assert ta_res["language"] == "ta"
    assert ta_res["supported"] is True
    assert ta_res["script"] == "tamil"

    # 3. Tamil-English Code-Mixed
    mixed_res = detect_language("My name is முருகன். Chennai Central பேருந்து நிலையம் அருகே my laptop was stolen.")
    assert mixed_res["language"] == "ta_en"
    assert mixed_res["supported"] is True
    assert mixed_res["is_multilingual"] is True

    # 4. Hindi (Explicitly out of scope)
    hi_res = detect_language("मेरा नाम राजेश शर्मा है और मेरी मोटरसाइकिल चोरी हो गई है।")
    assert hi_res["language"] == "hi"
    assert hi_res["supported"] is False
    assert "excluded" in hi_res["error"].lower()


def test_tamil_unicode_codepoint_invariants():
    """Verify exact character offset matching on native Tamil script."""
    tamil_complaint = (
        "என் பெயர் முருகன். 15/10/2026 அன்று மாலை 7:00 மணிக்கு சென்னை பேருந்து நிலையம் அருகே "
        "இரண்டு நபர்கள் என்னை இரும்புத் தடியால் தாக்கி ரூ. 45,000 மற்றும் தங்கச் சங்கிலியை பறித்துச் சென்றனர்."
    )

    # Test sentence segmentation
    spans = get_sentence_spans(tamil_complaint)
    assert len(spans) >= 2
    for sentence_text, s, e in spans:
        # Strict Unicode character codepoint invariant
        assert tamil_complaint[s:e] == sentence_text

    # Test exact needle spans
    needle_person = "முருகன்"
    span_person = find_exact_span(tamil_complaint, needle_person)
    assert span_person is not None
    s, e = span_person
    assert tamil_complaint[s:e] == needle_person

    needle_loc = "சென்னை பேருந்து நிலையம்"
    span_loc = find_exact_span(tamil_complaint, needle_loc)
    assert span_loc is not None
    assert tamil_complaint[span_loc[0]:span_loc[1]] == needle_loc

    needle_loss = "ரூ. 45,000"
    span_loss = find_exact_span(tamil_complaint, needle_loss)
    assert span_loss is not None
    assert tamil_complaint[span_loss[0]:span_loss[1]] == needle_loss


def test_tamil_information_extraction():
    """Verify entity and fact extraction on native Tamil legal complaint."""
    complaint_ta = (
        "புகார்தாரர் கதிரேசன். 20/10/2026 அன்று இரவு 9:00 மணிக்கு மதுரை அண்ணா நகர் அருகே "
        "தெரியாத நபர்கள் கத்தியால் தாக்கி எனது கைபேசி மற்றும் ரூ. 25,000 திருடினர்."
    )

    entities = _rule_based_entity_fallback(complaint_ta)
    assert len(entities) >= 3

    # Check invariant for all extracted entities
    for ent in entities:
        s = ent["start"]
        e = ent["end"]
        assert complaint_ta[s:e] == ent["entity_text"]

    facts = _extract_structured_facts(complaint_ta, entities)
    fact_types = {f["type"] for f in facts}

    assert "complainant" in fact_types or any(f["value"] == "கதிரேசன்" for f in facts)
    assert "incident_date" in fact_types
    assert "weapon_used" in fact_types or any("கத்தி" in f["value"] for f in facts)
    assert "loss" in fact_types

    # Verify offset invariant for all facts
    for f in facts:
        if f.get("start") is not None and f.get("end") is not None:
            s = f["start"]
            e = f["end"]
            assert complaint_ta[s:e] == f["value"] or f["value"] in complaint_ta[s:e]


def test_code_mixed_tamil_english_extraction():
    """Verify fact extraction on code-mixed Tamil-English text."""
    mixed_text = (
        "My name is K. Murugan. On 15/10/2026 at 8:30 PM near சென்னை பேருந்து நிலையம், "
        "two unknown men attacked me with an iron rod and stole my தங்கச் சங்கிலி and Rs. 30,000."
    )
    entities = _rule_based_entity_fallback(mixed_text)
    facts = _extract_structured_facts(mixed_text, entities)

    for f in facts:
        if f.get("start") is not None and f.get("end") is not None:
            assert mixed_text[f["start"]:f["end"]] == f["value"] or f["value"] in mixed_text[f["start"]:f["end"]]
