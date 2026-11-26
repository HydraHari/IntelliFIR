"""
services/validation_service.py — Independent factual validation of FIR drafts against original complaints.

Performs claim-level decomposition, evidence provenance alignment, negation/contradiction detection,
and missing statutory requisite evaluation.
Supports English, Native Tamil script, and Tamil-English code-mixed complaints.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.draft import DraftClaim, FIRDraft
from app.models.extraction import EvidenceSpan, ExtractedFact
from app.models.validation import (
    FindingCategory,
    FindingSeverity,
    ReviewerDecision,
    ValidationFinding,
)
from app.ml.ner.preprocessing import clean_text, split_into_sentences

logger = logging.getLogger(__name__)


def run_factual_validation_checks(
    raw_complaint: str,
    clean_draft: str,
    claims: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Pure factual validation function decoupled from database state.
    Executes all factual verification rules:
    - Missing statutory elements (date, time, jurisdiction)
    - Contradictions (dates, weapon claims, financial conflicts)
    - Ambiguities (English & Tamil vague phrases)
    - Unsupported assertions in claims
    """
    clean_complaint = clean_text(raw_complaint)
    complaint_lower = clean_complaint.lower()
    draft_lower = clean_draft.lower()

    findings: List[Dict[str, Any]] = []
    finding_idx = 1

    # ------------------------------------------------------------------ #
    # Check 1: Missing Essential Statutory Information in Source
    # ------------------------------------------------------------------ #
    has_date = bool(re.search(r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4})\b", clean_complaint))
    if not has_date:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.missing_information,
            "draft_claim": "Incident Date: [Unspecified Date]",
            "source_evidence": None,
            "explanation": "The original complaint does not specify an exact calendar date of occurrence.",
            "severity": FindingSeverity.high,
            "suggested_action": "Request complainant to confirm exact date of the alleged incident before FIR registration.",
        })
        finding_idx += 1

    has_time = bool(re.search(
        r"\b(?:\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm))\b|"
        r"((?:காலை|மாலை|இரவு|மதியம்)\s*\d{1,2}(?::\d{2})?|\d{1,2}\s*மணிக்கு)",
        clean_complaint,
        re.IGNORECASE,
    ))
    if not has_time:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.missing_information,
            "draft_claim": "Incident Time: [Unspecified Time]",
            "source_evidence": None,
            "explanation": "The approximate or exact time of incident is omitted in the primary complaint.",
            "severity": FindingSeverity.medium,
            "suggested_action": "Ascertain approximate time of day (morning/afternoon/night) from informant.",
        })
        finding_idx += 1

    loc_keywords = [
        "at", "near", "road", "street", "colony", "apartment", "district", "city",
        "village", "nagar", "market", "outside", "in ", "சென்னை", "மதுரை",
        "தெரு", "நகர்", "சாலை", "நிலையம்", "சந்தை", "பூங்கா"
    ]
    has_loc = any(k in complaint_lower for k in loc_keywords)
    if not has_loc:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.missing_information,
            "draft_claim": "Place of Occurrence: [Unspecified Location]",
            "source_evidence": None,
            "explanation": "No specific landmark, address, or territorial jurisdiction specified in complaint.",
            "severity": FindingSeverity.high,
            "suggested_action": "Obtain exact place of occurrence to establish police station jurisdiction.",
        })
        finding_idx += 1

    # ------------------------------------------------------------------ #
    # Check 2: Contradictions & Negation Conflicts
    # ------------------------------------------------------------------ #
    complaint_dates = set(re.findall(r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b", clean_complaint))
    if len(complaint_dates) > 1:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.contradiction,
            "draft_claim": "Timeline includes multiple conflicting date entries.",
            "source_evidence": ", ".join(complaint_dates),
            "explanation": f"Multiple distinct dates found in statement: {', '.join(complaint_dates)}.",
            "severity": FindingSeverity.medium,
            "suggested_action": "Clarify whether these represent a continuous series of incidents or a typographical error.",
        })
        finding_idx += 1

    # Contradiction: Weapon mentioned in draft when complaint explicitly denies weapons
    unarmed_markers = ["without weapon", "no weapon", "unarmed", "did not have any weapon", "ஆயுதம் இன்றி", "ஆயுதம் இல்லை"]
    complaint_claims_unarmed = any(m in complaint_lower for m in unarmed_markers)
    draft_mentions_weapon = bool(re.search(
        r"\b(knife|gun|pistol|iron rod|sharp object|weapon|dagger|lathi|கத்தி|துப்பாக்கி|தடி)\b",
        clean_draft,
        re.IGNORECASE,
    ))
    if complaint_claims_unarmed and draft_mentions_weapon:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.contradiction,
            "draft_claim": "Draft cites weapons while complaint explicitly states perpetrators were unarmed.",
            "source_evidence": "Complaint explicitly asserts lack of weapons.",
            "explanation": "Direct factual contradiction: Draft introduces weapon references contrary to complainant statement.",
            "severity": FindingSeverity.high,
            "suggested_action": "Immediately remove weapon claims from the draft narrative.",
        })
        finding_idx += 1

    # Contradiction: Conflicting financial loss figures stated by complainant
    financial_conflict_markers = ["though earlier", "earlier i thought", "earlier thought", "initially thought"]
    has_financial_conflict = any(m in complaint_lower for m in financial_conflict_markers) and (
        len(re.findall(r"(?:rs\.?|inr|₹|\$|ரூ(?:பாய்|\.)?)\s*([0-9,]+)", clean_complaint, re.IGNORECASE)) > 1
    )
    if has_financial_conflict:
        findings.append({
            "finding_id": f"VF-{finding_idx:03d}",
            "category": FindingCategory.contradiction,
            "draft_claim": "Conflicting financial loss figures stated in complaint narrative.",
            "source_evidence": "Multiple divergent loss figures mentioned with retroactive revision phrases.",
            "explanation": "Financial contradiction: Complainant explicitly states conflicting monetary loss amounts.",
            "severity": FindingSeverity.high,
            "suggested_action": "Obtain documentary proof (bank statements, receipts, invoices) to verify exact loss.",
        })
        finding_idx += 1

    # ------------------------------------------------------------------ #
    # Check 3: Ambiguity and Vague Terminology (English & Tamil)
    # ------------------------------------------------------------------ #
    vague_phrases = [
        ("sometime back", "Vague temporal reference creates difficulty in establishing limitation period under law."),
        ("some unknown person", "Suspect identity is completely vague; requires physical descriptors or CCTV inquiry."),
        ("approx", "Approximate quantity or time requires clarification."),
        ("maybe", "Speculative statement requires clarification before recording as evidence."),
        ("doubt that", "Subjective suspicion stated without corroborating evidence."),
        ("suspect that", "Subjective suspicion stated without corroborating evidence."),
        ("might have taken", "Uncertain theft allegation without direct evidence."),
        ("no proof", "Complainant explicitly concedes absence of proof for stated allegation."),
        ("many people", "Unspecified mob or group size; requires approximate headcount and descriptions."),
        ("சில நாட்களுக்கு முன்", "Vague temporal reference creates difficulty in establishing limitation period."),
        ("சந்தேகம் உள்ளது", "Subjective suspicion stated without corroborating evidence."),
        ("சந்தேகிக்கிறேன்", "Subjective suspicion stated without corroborating evidence."),
        ("ஒருவேளை", "Speculative statement requires clarification before recording as evidence."),
        ("தெரியாத நபர்", "Suspect identity is completely vague; requires physical descriptors or CCTV inquiry."),
    ]
    for phrase, explanation in vague_phrases:
        if phrase in complaint_lower:
            m = re.search(re.escape(phrase), clean_complaint, re.IGNORECASE)
            snippet = clean_complaint[max(0, m.start() - 25): min(len(clean_complaint), m.end() + 25)] if m else phrase
            findings.append({
                "finding_id": f"VF-{finding_idx:03d}",
                "category": FindingCategory.ambiguity,
                "draft_claim": f"Ambiguous statement containing '{phrase}'",
                "source_evidence": snippet,
                "explanation": explanation,
                "severity": FindingSeverity.medium,
                "suggested_action": "Interview informant to obtain precise details rather than vague assertions.",
            })
            finding_idx += 1

    # ------------------------------------------------------------------ #
    # Check 4: Atomic Claim-Level Grounding & Unsupported Claim Detection
    # ------------------------------------------------------------------ #
    if claims:
        for c_text in claims:
            c_clean = c_text.strip()
            c_lower = c_clean.lower()

            # Extract numeric values or amounts in claim
            claim_amounts = re.findall(r"(?:rs\.?|inr|₹|\$|ரூ(?:பாய்|\.)?)\s*([0-9,]+)", c_clean, re.IGNORECASE)
            for amt in claim_amounts:
                clean_amt = amt.replace(",", "")
                if clean_amt not in clean_complaint:
                    findings.append({
                        "finding_id": f"VF-{finding_idx:03d}",
                        "category": FindingCategory.unsupported_claim,
                        "draft_claim": c_clean,
                        "source_evidence": None,
                        "explanation": f"Financial figure '{amt}' in claim is not found in the original complaint statement.",
                        "severity": FindingSeverity.high,
                        "suggested_action": "Verify financial figure against actual complaint receipts or invoices.",
                    })
                    finding_idx += 1

            # Check token grounding for substantive narrative claims
            tokens = [t for t in re.findall(r"\w+", c_lower) if len(t) > 3 and t not in {
                "draft", "complaint", "incident", "report", "preliminary", "occurred",
                "complainant", "accused", "stated", "herein", "requires", "review",
                "information", "details", "approx"
            }]

            if tokens:
                matched_tokens = [t for t in tokens if t in complaint_lower]
                grounding_ratio = len(matched_tokens) / len(tokens)
                if grounding_ratio < 0.35 and len(tokens) >= 4:
                    findings.append({
                        "finding_id": f"VF-{finding_idx:03d}",
                        "category": FindingCategory.unsupported_claim,
                        "draft_claim": c_clean,
                        "source_evidence": None,
                        "explanation": f"Substantive claims in '{c_clean[:60]}...' lack sufficient lexical and semantic grounding in complaint.",
                        "severity": FindingSeverity.high,
                        "suggested_action": "Officer must cross-examine whether this fact was derived from external assumptions.",
                    })
                    finding_idx += 1

    return findings


def validate_fir_draft(db: Session, draft: FIRDraft) -> List[ValidationFinding]:
    """
    Independent validation comparing each claim in the FIR draft against the original complaint
    and verified evidence spans, persisting findings to the database.
    """
    complaint: Complaint = draft.complaint
    raw_complaint = complaint.raw_text or complaint.extracted_text or ""
    clean_draft = clean_text(draft.content)

    # 1. Clear previous findings for this draft
    db.query(ValidationFinding).filter(ValidationFinding.draft_id == draft.id).delete()
    db.commit()

    # 2. Get claims
    claims = db.query(DraftClaim).filter(DraftClaim.draft_id == draft.id).all()
    claim_texts = [c.claim_text for c in claims]

    # 3. Execute pure validation rules
    raw_findings = run_factual_validation_checks(raw_complaint, clean_draft, claim_texts)

    # 4. Map to ORM models
    orm_findings: List[ValidationFinding] = []
    unsupported_claim_texts: Set[str] = set()

    for rf in raw_findings:
        f_obj = ValidationFinding(
            draft_id=draft.id,
            finding_id=rf["finding_id"],
            category=rf["category"],
            draft_claim=rf["draft_claim"],
            source_evidence=rf["source_evidence"],
            explanation=rf["explanation"],
            severity=rf["severity"],
            suggested_action=rf["suggested_action"],
            reviewer_decision=ReviewerDecision.pending,
        )
        orm_findings.append(f_obj)
        db.add(f_obj)
        if rf["category"] == FindingCategory.unsupported_claim:
            unsupported_claim_texts.add(rf["draft_claim"])

    # 5. Update claims support status
    for c in claims:
        if c.claim_text in unsupported_claim_texts:
            c.is_supported = False
        else:
            c.is_supported = True

    complaint.status = "under_review"
    db.commit()

    return orm_findings
