"""
tests/test_clarification_and_validation.py — Tests for clarification questionnaire and validation logic.
"""
import uuid
import pytest
from app.services.clarification_service import generate_clarification_questionnaire


class MockComplaintForClarification:
    def __init__(self, raw_text: str, structured_data: dict):
        self.id = uuid.uuid4()
        self.reference_id = "CMP-UNC-001"
        self.raw_text = raw_text
        self.extracted_text = raw_text
        self.structured_data = structured_data


def test_clarification_missing_jurisdiction_and_time():
    raw = "My brown leather wallet was stolen sometime back."
    struct = {
        "complainant": "Anonymous",
        "incident": {
            "date": None,
            "time": None,
            "location": None,
        },
        "reported_persons": [],
        "unknown_accused": [],
    }
    complaint = MockComplaintForClarification(raw, struct)
    res = generate_clarification_questionnaire(complaint, struct, [])

    assert res["total_questions"] >= 2
    assert res["critical_count"] >= 1

    categories = {q["category"] for q in res["questions"]}
    assert "statutory_jurisdiction" in categories
    assert "timeline_precision" in categories

    for q in res["questions"]:
        assert len(q["prompt_question"]) > 10
        assert len(q["legal_rationale"]) > 10
        assert len(q["suggested_police_action"]) > 10


def test_clarification_unknown_accused():
    raw = "Two unidentified masked men attacked me near Park Street."
    struct = {
        "incident": {"date": "10/10/2026", "time": "9:00 PM", "location": "Park Street"},
        "unknown_accused": ["Two unidentified masked men"],
    }
    complaint = MockComplaintForClarification(raw, struct)
    res = generate_clarification_questionnaire(complaint, struct, [])

    categories = {q["category"] for q in res["questions"]}
    assert "suspect_identification" in categories
