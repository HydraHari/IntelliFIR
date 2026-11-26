"""
services/draft_service.py — FIR Draft generation (template-based and LLM-assisted) and document export.
"""
from __future__ import annotations

import io
import logging
import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.complaint import Complaint
    from app.models.draft import FIRDraft

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "AI-GENERATED DRAFT — REQUIRES AUTHORIZED HUMAN REVIEW\n"
    "This document is an AI-assisted preliminary draft compiled strictly from the complainant's statement.\n"
    "It does not constitute an official FIR registration, nor does it establish legal guilt or final determinations."
)


def generate_fir_draft(
    db: Any,
    complaint: Any,
    user_id: uuid.UUID,
    method: str = "template",
) -> Any:
    """
    Generate a structured First Information Report (FIR) draft from extracted facts.
    """
    from app.models.draft import FIRDraft, DraftClaim
    from app.models.extraction import ExtractedFact, EvidenceSpan
    from app.ml.llm.ollama_provider import ollama_provider
    from app.core.config import settings
    # 1. Fetch facts and evidence spans
    facts: List[ExtractedFact] = (
        db.query(ExtractedFact).filter(ExtractedFact.complaint_id == complaint.id).all()
    )
    structured_data = complaint.structured_data or {}

    # 2. Increment version number
    current_version = (
        db.query(FIRDraft)
        .filter(FIRDraft.complaint_id == complaint.id)
        .count()
    ) + 1

    # 3. Mark previous drafts as non-current
    db.query(FIRDraft).filter(FIRDraft.complaint_id == complaint.id).update(
        {"is_current": False}
    )

    # 4. Generate content
    draft_title = f"DRAFT FIR: {complaint.reference_id} — {complaint.title}"
    content = ""
    used_method = method

    if method in ["llm", "hybrid"] and settings.LLM_PROVIDER == "ollama":
        try:
            content = _generate_llm_draft(complaint, structured_data, facts)
            used_method = "llm"
        except Exception as exc:
            logger.warning("LLM generation failed, falling back to template: %s", exc)
            content = _generate_template_draft(complaint, structured_data, facts)
            used_method = "template"
    else:
        content = _generate_template_draft(complaint, structured_data, facts)
        used_method = "template"

    # 5. Persist FIRDraft
    fir_draft = FIRDraft(
        complaint_id=complaint.id,
        version=current_version,
        title=draft_title,
        content=content,
        structured_draft=structured_data,
        generation_method=used_method,
        is_current=True,
        created_by_id=user_id,
    )
    db.add(fir_draft)
    db.flush()

    # 6. Extract atomic claims from the draft for factual validation
    _create_draft_claims(db, fir_draft, content, facts)

    complaint.status = "validation_required"
    db.commit()
    db.refresh(fir_draft)

    return fir_draft


def _generate_template_draft(
    complaint: Complaint, structured_data: Dict[str, Any], facts: List[ExtractedFact]
) -> str:
    """Generate deterministic, fact-grounded template FIR draft."""
    incident = structured_data.get("incident", {})
    complainant = structured_data.get("complainant") or "[Not specified in complaint — Human verification required]"
    reported_persons = structured_data.get("reported_persons", [])
    witnesses = structured_data.get("witnesses", [])
    evidence = structured_data.get("reported_evidence", [])
    missing = structured_data.get("missing_details", [])
    uncertain = structured_data.get("uncertain_details", [])

    date_str = incident.get("date") or "[Unspecified Date]"
    time_str = incident.get("time") or "[Unspecified Time]"
    loc_str = incident.get("location") or "[Unspecified Location]"

    suspects_str = ", ".join(reported_persons) if reported_persons else "[Unknown / Not explicitly identified]"
    witnesses_str = ", ".join(witnesses) if witnesses else "[None mentioned in complaint]"
    evidence_str = ", ".join(evidence) if evidence else "[No physical/electronic evidence explicitly cited]"
    missing_str = "\n".join(f"- {m}" for m in missing) if missing else "- None identified by automated inspection."
    uncertain_str = "\n".join(f"- {u}" for u in uncertain) if uncertain else "- None."

    raw_statement = complaint.raw_text or complaint.extracted_text or ""
    # Truncate statement cleanly for narrative body if lengthy
    narrative_body = raw_statement.strip()

    sections = [
        "=" * 70,
        "PRELIMINARY FIRST INFORMATION REPORT (FIR) — DRAFT",
        DISCLAIMER_TEXT,
        "=" * 70,
        "",
        f"1. COMPLAINT REFERENCE ID: {complaint.reference_id}",
        f"2. FILING DATE/TIME:        {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"3. COMPLAINANT / INFORMANT: {complainant}",
        "",
        "4. OCCURRENCE OF OFFENCE:",
        f"   - Date of Incident:      {date_str}",
        f"   - Time of Incident:      {time_str}",
        f"   - Place of Occurrence:   {loc_str}",
        "",
        "5. PERSONS & WITNESSES INVOLVED:",
        f"   - Reported Persons/Suspects: {suspects_str}",
        f"   - Witnesses Mentioned:       {witnesses_str}",
        "",
        "6. REPORTED EVIDENCE & ASSETS:",
        f"   - Evidence Mentioned:    {evidence_str}",
        "",
        "7. STATEMENT / INCIDENT NARRATIVE (AS REPORTED BY COMPLAINANT):",
        f"   {narrative_body}",
        "",
        "8. UNCERTAIN / ALLEGED DETAILS (REQUIRING CORROBORATION):",
        uncertain_str,
        "",
        "9. MISSING / INCOMPLETE DETAILS (ACTION ITEM FOR INVESTIGATOR):",
        missing_str,
        "",
        "10. REVIEWER NOTES & INVESTIGATION CHECKLIST:",
        "   - [ ] Verify complainant identity and contact credentials.",
        "   - [ ] Obtain formal written statement or signature.",
        "   - [ ] Ascertain exact scene coordinates and jurisdiction.",
        "   - [ ] Secure CCTV / electronic evidence if mentioned.",
        "",
        "=" * 70,
        "END OF DRAFT — AWAITING AUTHORIZED OFFICER REVIEW",
        "=" * 70,
    ]

    return "\n".join(sections)


def _generate_llm_draft(
    complaint: Complaint, structured_data: Dict[str, Any], facts: List[ExtractedFact]
) -> str:
    """Generate FIR draft using local Ollama model with strict anti-hallucination prompt."""
    prompt = f"""You are an expert legal assistant drafting a preliminary First Information Report (FIR) based strictly on a citizen's complaint.

CRITICAL INSTRUCTIONS:
1. ONLY use facts directly present in the source information below.
2. DO NOT invent, extrapolate, or assume names, dates, locations, or weapons.
3. If an item is missing, explicitly write [MISSING - Requires Clarification].
4. Do NOT determine guilt or make definitive judicial conclusions.
5. Maintain a neutral, formal, objective tone.
6. Begin with the disclaimer: 'AI-GENERATED DRAFT — REQUIRES AUTHORIZED HUMAN REVIEW'.

SOURCE INFORMATION:
- Reference ID: {complaint.reference_id}
- Complainant: {structured_data.get('complainant', 'Unspecified')}
- Incident Date: {structured_data.get('incident', {}).get('date', 'Unspecified')}
- Incident Time: {structured_data.get('incident', {}).get('time', 'Unspecified')}
- Incident Location: {structured_data.get('incident', {}).get('location', 'Unspecified')}
- Reported Suspects/Persons: {', '.join(structured_data.get('reported_persons', [])) or 'None identified'}
- Witnesses: {', '.join(structured_data.get('witnesses', [])) or 'None'}
- Evidence: {', '.join(structured_data.get('reported_evidence', [])) or 'None'}

COMPLAINT STATEMENT:
{complaint.raw_text or complaint.extracted_text}

Generate the structured FIR Draft following standard police reporting format with clear sections:
1. Title and Disclaimer
2. General Information
3. Incident Occurrence
4. Persons Involved
5. Reported Facts & Narrative
6. Identified Evidence
7. Missing/Uncertain Details
"""
    response = ollama_provider.generate(prompt)
    if not response or len(response.strip()) < 100:
        raise ValueError("Ollama generated empty or invalid response")
    return response


def _create_draft_claims(
    db: Session, draft: FIRDraft, content: str, facts: List[ExtractedFact]
) -> None:
    """Deconstruct draft into verifiable propositions linked to evidence spans."""
    from app.models.draft import DraftClaim
    from app.models.extraction import EvidenceSpan

    evidence_spans: List[EvidenceSpan] = (
        db.query(EvidenceSpan)
        .filter(EvidenceSpan.complaint_id == draft.complaint_id)
        .all()
    )

    lines = [l.strip() for l in content.split("\n") if l.strip()]
    claim_lines = [
        l for l in lines
        if not l.startswith("=")
        and not l.startswith("---")
        and "DISCLAIMER" not in l
        and len(l) > 12
    ]

    for line in claim_lines[:35]:  # Up to 35 atomic claims
        line_clean = line.lstrip("- *0123456789.[]()").strip()
        if not line_clean or len(line_clean) < 10:
            continue

        ctype = "narrative"
        lower = line_clean.lower()
        if "complainant" in lower or "informant" in lower:
            ctype = "complainant"
        elif "date" in lower or "time" in lower or "occurred" in lower:
            ctype = "occurrence"
        elif "location" in lower or "place" in lower or "scene" in lower:
            ctype = "location"
        elif "suspect" in lower or "accused" in lower or "attacker" in lower:
            ctype = "suspect"
        elif "weapon" in lower or "knife" in lower or "rod" in lower or "gun" in lower:
            ctype = "weapon"
        elif "stolen" in lower or "property" in lower or "loss" in lower or "rs." in lower:
            ctype = "property_loss"
        elif "injury" in lower or "bleeding" in lower or "hospital" in lower:
            ctype = "injury"
        elif "cctv" in lower or "evidence" in lower or "witness" in lower:
            ctype = "evidence"

        # Find best matching evidence span
        matched_span_id = None
        best_overlap = 0

        claim_tokens = set(re.findall(r"\w+", lower))
        for span in evidence_spans:
            if not span.original_text:
                continue
            span_lower = span.original_text.lower()
            if span_lower in lower or lower in span_lower:
                matched_span_id = span.id
                break

            span_tokens = set(re.findall(r"\w+", span_lower))
            overlap = len(claim_tokens.intersection(span_tokens))
            if overlap > best_overlap and overlap >= 2:
                best_overlap = overlap
                matched_span_id = span.id

        claim = DraftClaim(
            draft_id=draft.id,
            claim_text=line_clean,
            claim_type=ctype,
            evidence_span_id=matched_span_id,
            is_supported=None,  # Evaluated by validation service
        )
        db.add(claim)


def export_draft_pdf(draft: FIRDraft) -> io.BytesIO:
    """Generate professional legal PDF document for FIR draft with provenance notices."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,  # Centered
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#B45309"),
        alignment=1,
    )
    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Title
    story.append(Paragraph("INTELLIFIR — PRELIMINARY FIRST INFORMATION REPORT", title_style))
    story.append(Spacer(1, 6))

    # Official Disclaimer Box
    disclaimer_p = Paragraph(
        "<b>LEGAL DISCLAIMER: AI-ASSISTED PRELIMINARY DRAFT — REQUIRES AUTHORIZED HUMAN REVIEW</b><br/>"
        "This document is compiled strictly from the complainant's statement using natural language processing. "
        "It does not constitute an officially registered FIR, nor does it establish legal guilt or judicial determinations.",
        disclaimer_style,
    )
    disc_table = Table([[disclaimer_p]], colWidths=[530])
    disc_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
            ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(disc_table)
    story.append(Spacer(1, 10))

    # Meta banner
    gen_time = draft.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if draft.created_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    meta_table_data = [
        [
            Paragraph(f"<b>Draft Version:</b> {draft.version}", meta_style),
            Paragraph(f"<b>Generation Method:</b> {draft.generation_method.upper()}", meta_style),
            Paragraph(f"<b>Generated On:</b> {gen_time}", meta_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[175, 175, 180])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Draft content parsed by lines
    lines = draft.content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("="):
            continue
        if stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=4, spaceAfter=4))
            continue

        # Detect headers vs content
        if re.match(r"^\d+\.\s+[A-Z\s/()—]+:", stripped) or stripped.isupper() and len(stripped) < 60:
            story.append(Paragraph(stripped, heading_style))
        else:
            safe_text = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_text, body_style))

    # Signature Block
    story.append(Spacer(1, 20))
    sig_data = [
        [
            Paragraph("<b>Investigating / Reporting Officer:</b><br/><br/>____________________________<br/>Name: <br/>Rank / Badge ID: <br/>Police Station: ", meta_style),
            Paragraph("<b>Station House Officer (SHO) Authorization:</b><br/><br/>____________________________<br/>Signature &amp; Official Seal<br/>Date: ", meta_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[265, 265])
    sig_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(sig_table)

    doc.build(story)
    buf.seek(0)
    return buf


def export_draft_docx(draft: FIRDraft) -> io.BytesIO:
    """Generate Word (.docx) document for FIR draft."""
    import docx
    from docx.shared import Inches, Pt, RGBColor

    doc = docx.Document()
    title = doc.add_heading("IntelliFIR — Draft First Information Report", 0)
    title.style.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)

    # Disclaimer Callout
    p_disc = doc.add_paragraph()
    r_disc = p_disc.add_run(DISCLAIMER_TEXT)
    r_disc.bold = True
    r_disc.font.color.rgb = RGBColor(0xD9, 0x77, 0x06)

    doc.add_paragraph(f"Draft Version: {draft.version} | Generated: {draft.created_at.strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph("-" * 50)

    for line in draft.content.split("\n"):
        if line.startswith("="):
            continue
        p = doc.add_paragraph(line)
        p.paragraph_format.space_after = Pt(2)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
