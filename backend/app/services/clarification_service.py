"""
services/clarification_service.py — Uncertainty quantification and clarification question generation.

Translates missing statutory information, ungrounded claims, and factual ambiguities
into structured investigative prompts for investigating officers under BNSS Section 173 / CrPC 154.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


def generate_clarification_questionnaire(
    complaint: Any,
    structured_data: Optional[Dict[str, Any]] = None,
    validation_findings: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Generate prioritized investigative questions addressing information gaps,
    missing statutory requisites, and factual uncertainties.
    """
    raw_text = complaint.raw_text or complaint.extracted_text or ""
    clean_lower = raw_text.lower()
    data = structured_data or complaint.structured_data or {}
    incident = data.get("incident", {})

    questions: List[Dict[str, Any]] = []
    q_idx = 1

    # 1. Statutory Jurisdiction / Scene of Crime Check
    loc = incident.get("location")
    if not loc or loc.startswith("[Unspecified") or len(loc) < 3:
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "statutory_jurisdiction",
            "priority": "CRITICAL",
            "target_entity": "Place of Occurrence / Jurisdiction",
            "prompt_question": "Where exactly did the incident take place? Please provide the precise street address, landmark, or GPS coordinates.",
            "legal_rationale": "Mandatory to determine local territorial jurisdiction of the Police Station under Section 173 BNSS.",
            "suggested_police_action": "Conduct immediate spot inspection and draw rough site plan (Draft Sketch).",
        })
        q_idx += 1

    # 2. Timeline Precision Check
    incident_date = incident.get("date")
    incident_time = incident.get("time")
    if not incident_date or incident_date.startswith("[Unspecified"):
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "timeline_precision",
            "priority": "CRITICAL",
            "target_entity": "Date of Offence",
            "prompt_question": "On what calendar date did the alleged occurrence happen?",
            "legal_rationale": "Mandatory under Column 5 of Form FIR; essential for limitation and alibi evaluation.",
            "suggested_police_action": "Verify date against CDR, digital timestamps, or medical admission records.",
        })
        q_idx += 1

    if not incident_time or incident_time.startswith("[Unspecified"):
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "timeline_precision",
            "priority": "HIGH",
            "target_entity": "Time of Occurrence",
            "prompt_question": "At approximately what time did the offence occur (e.g., exact hour or morning/evening)?",
            "legal_rationale": "Necessary to distinguish day-time house-trespass from night lurking house-trespass under BNS.",
            "suggested_police_action": "Cross-reference with nearest CCTV footage time stamps and traffic camera feeds.",
        })
        q_idx += 1

    # 3. Accused & Suspect Particulars
    reported_persons = data.get("reported_persons", [])
    unknown_accused = data.get("unknown_accused", [])

    if not reported_persons and not unknown_accused:
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "suspect_identification",
            "priority": "CRITICAL",
            "target_entity": "Perpetrator Identity",
            "prompt_question": "Were the offenders known to you, or were they unidentified individuals?",
            "legal_rationale": "Required under Column 7 of FIR to record Known / Suspected / Unknown accused.",
            "suggested_police_action": "Record detailed physical descriptions: approximate age, height, attire, accents, or distinctive scars.",
        })
        q_idx += 1
    elif unknown_accused:
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "suspect_identification",
            "priority": "HIGH",
            "target_entity": "Unknown Perpetrators",
            "prompt_question": "Can you describe the physical features, vehicle registration numbers, or direction of flight of the attackers?",
            "legal_rationale": "Critical for Test Identification Parade (TIP) and flash message alert dispatch.",
            "suggested_police_action": "Request forensic portrait artist and issue border/toll naka alert for vehicle.",
        })
        q_idx += 1

    # 4. Weapons & Force Used
    weapons = data.get("weapons_used", [])
    if any(w in clean_lower for w in ["assaulted", "hit", "attacked", "stabbed"]) and not weapons:
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "evidence_chain",
            "priority": "HIGH",
            "target_entity": "Weapon of Offence",
            "prompt_question": "Did the perpetrator use any weapon (e.g. knife, firearm, blunt object, stick), or bare hands?",
            "legal_rationale": "Determines application of aggravated sections (e.g., Section 115 vs 118 BNS for dangerous weapons).",
            "suggested_police_action": "Instruct investigating officer to prepare seizure memo for any discarded objects at scene.",
        })
        q_idx += 1

    # 5. Stolen Property / Financial Loss Substantiation
    losses = data.get("loss_information", [])
    properties = data.get("property_involved", [])
    if (losses or properties) and not any(w in clean_lower for w in ["invoice", "receipt", "bill", "imei", "serial"]):
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "loss_quantification",
            "priority": "MEDIUM",
            "target_entity": "Property Verification",
            "prompt_question": "Do you possess purchase invoices, bank statements, or IMEI numbers for the stolen property?",
            "legal_rationale": "Required for property seizure documentation under Section 106 BNSS.",
            "suggested_police_action": "Collect tax invoice copies and block IMEI on CEIR portal.",
        })
        q_idx += 1

    # 6. Physical Injuries & Medical Evidence
    injuries = data.get("injury_information", [])
    if injuries and not any(w in clean_lower for w in ["hospital", "doctor", "mlc", "treatment"]):
        questions.append({
            "id": f"CQ-{q_idx:02d}",
            "category": "evidence_chain",
            "priority": "HIGH",
            "target_entity": "Medico-Legal Evidence",
            "prompt_question": "Did you receive medical treatment or an injury certificate from a government or private hospital?",
            "legal_rationale": "Mandatory to corroborate physical hurt with Medico-Legal Certificate (MLC).",
            "suggested_police_action": "Refer victim immediately to nearest Government Hospital for formal medical examination.",
        })
        q_idx += 1

    # 7. Ambiguities & Subjective Suspicions from Validation Findings
    if validation_findings:
        for f in validation_findings:
            if getattr(f, "category", None) in ["ambiguity", "uncertainty"]:
                questions.append({
                    "id": f"CQ-{q_idx:02d}",
                    "category": "ambiguity_resolution",
                    "priority": "MEDIUM",
                    "target_entity": "Factual Clarification",
                    "prompt_question": f"Regarding statement '{getattr(f, 'draft_claim', '')}': Please clarify the specific factual basis for this assertion.",
                    "legal_rationale": getattr(f, "explanation", "Vague claims cannot form basis of statutory penal charges."),
                    "suggested_police_action": getattr(f, "suggested_action", "Clarify during complainant examination."),
                })
                q_idx += 1

    critical_count = sum(1 for q in questions if q["priority"] == "CRITICAL")

    return {
        "complaint_id": complaint.id,
        "reference_id": complaint.reference_id,
        "total_questions": len(questions),
        "critical_count": critical_count,
        "questions": questions,
    }
