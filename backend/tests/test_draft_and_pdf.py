"""
tests/test_draft_and_pdf.py — Tests for draft compilation, atomic claims, and PDF/DOCX export.
"""
import uuid
from datetime import datetime
import pytest

from app.services.draft_service import (
    DISCLAIMER_TEXT,
    _generate_template_draft,
    export_draft_docx,
    export_draft_pdf,
)


class MockComplaint:
    def __init__(self):
        self.id = uuid.uuid4()
        self.reference_id = "CMP-2026-TEST"
        self.title = "Theft of Laptop"
        self.raw_text = "I, Ramesh Gupta, report that my laptop was stolen from Sector 15 on 12/08/2026."
        self.extracted_text = self.raw_text
        self.incident_date = datetime(2026, 8, 12)
        self.incident_location = "Sector 15"
        self.structured_data = {
            "complainant": "Ramesh Gupta",
            "incident": {
                "date": "12/08/2026",
                "time": "8:30 PM",
                "location": "Sector 15",
            },
            "reported_persons": ["Mohit Yadav"],
            "witnesses": ["Suresh Kumar"],
            "reported_evidence": ["CCTV"],
            "property_involved": ["HP Laptop"],
            "loss_information": ["Rs. 65,000"],
            "missing_details": [],
            "uncertain_details": [],
        }


class MockDraft:
    def __init__(self, content: str):
        self.id = uuid.uuid4()
        self.version = 1
        self.title = "Draft FIR: CMP-2026-TEST"
        self.content = content
        self.generation_method = "template"
        self.created_at = datetime.utcnow()


def test_generate_template_draft_disclaimer():
    complaint = MockComplaint()
    draft_content = _generate_template_draft(complaint, complaint.structured_data, [])

    # Strict compliance: Disclaimer must be present
    assert "AI-GENERATED DRAFT" in draft_content
    assert "REQUIRES AUTHORIZED HUMAN REVIEW" in draft_content
    assert "Ramesh Gupta" in draft_content
    assert "Mohit Yadav" in draft_content
    assert "Sector 15" in draft_content


def test_export_draft_pdf():
    complaint = MockComplaint()
    draft_content = _generate_template_draft(complaint, complaint.structured_data, [])
    draft = MockDraft(draft_content)

    pdf_buffer = export_draft_pdf(draft)
    pdf_bytes = pdf_buffer.getvalue()

    # Valid PDF file header: %PDF
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_export_draft_docx():
    complaint = MockComplaint()
    draft_content = _generate_template_draft(complaint, complaint.structured_data, [])
    draft = MockDraft(draft_content)

    docx_buffer = export_draft_docx(draft)
    docx_bytes = docx_buffer.getvalue()

    # Valid docx zip header: PK\x03\x04
    assert len(docx_bytes) > 500
    assert docx_bytes.startswith(b"PK\x03\x04")
