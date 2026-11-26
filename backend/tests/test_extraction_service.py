"""
tests/test_extraction_service.py — Tests for legal information extraction and span alignment.
"""
import pytest
from app.services.extraction_service import (
    _extract_structured_facts,
    _rule_based_entity_fallback,
)


def test_rule_based_entity_extraction():
    text = (
        "I, Ramesh Gupta, state that on 12/08/2026 at 8:30 PM outside Sunrise Apartments, "
        "accused Mohit Yadav stole Rs. 65,000."
    )
    entities = _rule_based_entity_fallback(text)
    assert len(entities) > 0

    # Verify offset invariant for all entities
    for ent in entities:
        s = ent["start"]
        e = ent["end"]
        assert text[s:e] == ent["entity_text"]

    types = {e["entity_type"] for e in entities}
    assert "DATE" in types or "TIME" in types or "PERSON" in types


def test_structured_facts_extraction():
    text = (
        "My name is Rajesh Sharma. On 14/09/2026 at 10:15 PM outside Grand Mall, MG Road, "
        "two unknown men struck me with an iron rod causing severe bleeding. "
        "Witness Suresh Kumar saw them snatch my gold chain worth Rs. 90,000. CCTV recorded this."
    )
    entities = _rule_based_entity_fallback(text)
    facts = _extract_structured_facts(text, entities)

    fact_types = {f["type"] for f in facts}
    assert "complainant" in fact_types
    assert "weapon_used" in fact_types
    assert "property" in fact_types
    assert "loss" in fact_types
    assert "injury" in fact_types
    assert "evidence" in fact_types

    # Test invariant for facts with offsets
    for f in facts:
        if f.get("start") is not None and f.get("end") is not None:
            val = f["value"]
            s = f["start"]
            e = f["end"]
            assert text[s:e] == val or val in text[s:e]
