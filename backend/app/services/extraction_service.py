"""
services/extraction_service.py — NER and structured information extraction with evidence provenance.

Supports English, Native Tamil script, and Tamil-English code-mixed complaints.
Guarantees strict character-level provenance invariant:
    raw_text[span.start_offset : span.end_offset] == span.original_text
where offsets represent Python Unicode character indices.
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from app.ml.ner.preprocessing import (
    clean_text,
    detect_language,
    find_exact_span,
    get_sentence_spans,
    split_into_sentences,
)

logger = logging.getLogger(__name__)

# Common location keywords in English and Tamil to disambiguate locations from persons
LOCATION_INDICATORS = {
    "apartments", "apartment", "sector", "road", "street", "colony", "chowk",
    "nagar", "market", "station", "lines", "mall", "phase", "block", "town",
    "bus stand", "terminus", "bazaar", "park", "expressway", "cross", "lane",
    "சென்னை", "மதுரை", "கோயம்புத்தூர்", "திருச்சி", "சேலம்", "தெரு", "நகர்",
    "சாலை", "நிலையம்", "சந்தை", "பூங்கா", "வளாகம்"
}

SKIP_CAP_WORDS = {
    "the", "this", "that", "there", "yesterday", "today", "tomorrow",
    "near", "about", "around", "police", "station", "officer", "fir",
    "sir", "madam", "court", "complaint", "incident", "hospital", "statement",
    "details", "information", "end", "draft", "preliminary", "review",
    "காலை", "மாலை", "இரவு", "அன்று", "நேற்று", "இன்று", "நாளை"
}


def process_complaint_pipeline(db: Any, complaint: Any) -> Dict[str, Any]:
    """
    Execute full information extraction pipeline on complaint text:
    1. Language detection & offset validation
    2. BERT / Legal Named Entity Recognition
    3. Structured legal facts & role attribution
    4. Evidence provenance linking with invariant verification
    5. Persistence to database
    """
    from app.models.extraction import EvidenceSpan, ExtractedEntity, ExtractedFact
    from app.ml.ner.ner_service import ner_service

    raw_text = complaint.raw_text or complaint.extracted_text or ""
    if not raw_text.strip():
        logger.warning("Complaint %s has empty text; skipping extraction.", complaint.id)
        return {}

    lang_meta = detect_language(raw_text)

    # 1. Clear previous extractions if reprocessing
    db.query(EvidenceSpan).filter(EvidenceSpan.complaint_id == complaint.id).delete()
    db.query(ExtractedFact).filter(ExtractedFact.complaint_id == complaint.id).delete()
    db.query(ExtractedEntity).filter(ExtractedEntity.complaint_id == complaint.id).delete()
    db.commit()

    # 2. Extract Entities using BERT NER or Rule-based fallback
    raw_entities: List[dict] = []
    # If text is primarily Tamil or BERT is not available, use enhanced rule fallback
    if lang_meta["language"] in ["ta", "ta_en"]:
        raw_entities = _rule_based_entity_fallback(raw_text)
    else:
        try:
            raw_entities = ner_service.extract_entities(raw_text)
        except Exception as exc:
            logger.warning("BERT NER execution failed; falling back to rule-based entity extraction: %s", exc)
            raw_entities = _rule_based_entity_fallback(raw_text)

    # If BERT returned few entities, enrich with rule-based fallback
    if len(raw_entities) < 2:
        fallback_ents = _rule_based_entity_fallback(raw_text)
        existing_spans = {(e["start"], e["end"]) for e in raw_entities}
        for fe in fallback_ents:
            if (fe["start"], fe["end"]) not in existing_spans:
                raw_entities.append(fe)

    # Persist ExtractedEntity records with verified offsets
    for ent in raw_entities:
        e_text = ent["entity_text"]
        s_off = ent["start"]
        e_off = ent["end"]

        # Invariant check: if not matching raw_text, re-align
        if e_off > len(raw_text) or raw_text[s_off:e_off] != e_text:
            aligned = find_exact_span(raw_text, e_text)
            if aligned:
                s_off, e_off = aligned
                e_text = raw_text[s_off:e_off]

        e_obj = ExtractedEntity(
            complaint_id=complaint.id,
            entity_text=e_text,
            entity_type=ent["entity_type"],
            start_offset=s_off,
            end_offset=e_off,
            source_sentence=ent.get("source_sentence"),
            confidence=ent.get("score", 0.9),
            extraction_method=ent.get("extraction_method", "rule-ner"),
        )
        db.add(e_obj)

    # 3. Information Extraction (Structured Facts)
    facts_data = _extract_structured_facts(raw_text, raw_entities)

    structured_case: Dict[str, Any] = {
        "complaint_id": complaint.reference_id,
        "language_meta": lang_meta,
        "complainant": None,
        "reported_persons": [],
        "unknown_accused": [],
        "victim": None,
        "witnesses": [],
        "incident": {
            "date": complaint.incident_date.isoformat() if complaint.incident_date else None,
            "time": None,
            "location": complaint.incident_location,
            "description": "",
        },
        "offence_acts": [],
        "weapons_used": [],
        "property_involved": [],
        "loss_information": [],
        "injury_information": [],
        "reported_evidence": [],
        "uncertain_details": [],
        "missing_details": [],
    }

    for f in facts_data:
        s_off = f.get("start")
        e_off = f.get("end")
        source_val = f.get("value", "")

        # Verify invariant against raw text
        if s_off is not None and e_off is not None:
            if e_off > len(raw_text) or raw_text[s_off:e_off] != source_val:
                aligned = find_exact_span(raw_text, source_val)
                if aligned:
                    s_off, e_off = aligned

        fact_obj = ExtractedFact(
            complaint_id=complaint.id,
            fact_type=f["type"],
            fact_value=source_val,
            source_span_start=s_off,
            source_span_end=e_off,
            source_text=f.get("source_text") or (raw_text[s_off:e_off] if s_off is not None else None),
            is_certain=f.get("is_certain", True),
            confidence=f.get("confidence", 0.9),
        )
        db.add(fact_obj)
        db.flush()  # assign fact_obj.id

        # 4. Evidence Provenance Link
        if s_off is not None and e_off is not None:
            original_span_text = raw_text[s_off:e_off]
            span_obj = EvidenceSpan(
                complaint_id=complaint.id,
                fact_id=fact_obj.id,
                original_text=original_span_text,
                start_offset=s_off,
                end_offset=e_off,
                source_sentence=f.get("source_text"),
                extraction_method=f.get("method", "evidence-provenance-extractor"),
            )
            db.add(span_obj)

        _update_structured_json(structured_case, f)

    complaint.structured_data = structured_case
    complaint.status = "draft_generated" if complaint.status == "processing" else complaint.status
    db.commit()

    return structured_case


def _update_structured_json(case: Dict[str, Any], fact: Dict[str, Any]) -> None:
    ftype = fact["type"]
    val = fact["value"]
    is_certain = fact.get("is_certain", True)

    if ftype == "complainant" and not case.get("complainant"):
        case["complainant"] = val
    elif ftype == "victim" and not case.get("victim"):
        case["victim"] = val
    elif ftype in ["accused", "suspect", "reported_person"]:
        if is_certain:
            if val not in case["reported_persons"]:
                case["reported_persons"].append(val)
        else:
            unc_entry = f"Suspect: {val} (alleged/suspected)"
            if unc_entry not in case["uncertain_details"]:
                case["uncertain_details"].append(unc_entry)
    elif ftype == "unknown_accused":
        if val not in case["unknown_accused"]:
            case["unknown_accused"].append(val)
    elif ftype == "witness":
        if val not in case["witnesses"]:
            case["witnesses"].append(val)
    elif ftype == "incident_location" and not case["incident"]["location"]:
        case["incident"]["location"] = val
    elif ftype == "incident_date" and not case["incident"]["date"]:
        case["incident"]["date"] = val
    elif ftype == "incident_time" and not case["incident"]["time"]:
        case["incident"]["time"] = val
    elif ftype == "offence_act":
        if val not in case["offence_acts"]:
            case["offence_acts"].append(val)
    elif ftype == "weapon_used":
        if val not in case["weapons_used"]:
            case["weapons_used"].append(val)
    elif ftype == "evidence":
        if val not in case["reported_evidence"]:
            case["reported_evidence"].append(val)
    elif ftype == "property":
        if val not in case["property_involved"]:
            case["property_involved"].append(val)
    elif ftype == "loss":
        if val not in case["loss_information"]:
            case["loss_information"].append(val)
    elif ftype == "injury":
        if val not in case["injury_information"]:
            case["injury_information"].append(val)
    elif ftype == "missing_detail":
        if val not in case["missing_details"]:
            case["missing_details"].append(val)
    elif not is_certain:
        if val not in case["uncertain_details"]:
            case["uncertain_details"].append(val)


def _extract_structured_facts(raw_text: str, entities: List[dict]) -> List[Dict[str, Any]]:
    """Extract structured legal facts with verified offsets against raw_text."""
    facts: List[Dict[str, Any]] = []

    # A. Complainant detection (English + Native Tamil)
    complainant_patterns = [
        # English patterns
        r"(?:my name is|i am|i,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:complainant|informant|undersigned)\s*(?:is|:|,)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:complaint of|statement of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        # Tamil patterns
        r"(?:என்\s+பெயர்|புகார்தாரர்)\s*[:—\-]?\s*([^\n,.;]+?)(?:\s*ஆகிய\s*நான்|\s*என்பவர்|\.|\n|,|$)",
        r"(?:நான்\s+)([^\n,.;]+?)(?:\s*என்பவர்|\s*வசித்து\s*வருகிறேன்)",
    ]
    for pat in complainant_patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            c_name = m.group(1).strip()
            # Avoid long strings
            if 2 < len(c_name) < 45:
                span = find_exact_span(raw_text, c_name, m.start(1), m.end(1))
                if span:
                    facts.append({
                        "type": "complainant",
                        "value": c_name,
                        "start": span[0],
                        "end": span[1],
                        "source_text": m.group(0),
                        "is_certain": True,
                        "confidence": 0.95,
                        "method": "pattern-match",
                    })
                    break

    # First PERSON entity in context if not matched by pattern
    if not any(f["type"] == "complainant" for f in facts):
        persons = [e for e in entities if e["entity_type"] == "PERSON"]
        if persons:
            p = persons[0]
            facts.append({
                "type": "complainant",
                "value": p["entity_text"],
                "start": p["start"],
                "end": p["end"],
                "source_text": p.get("source_sentence", p["entity_text"]),
                "is_certain": False,
                "confidence": 0.70,
                "method": "ner-first-person",
            })

    # B. Suspects, Unknown Accused, Witnesses, Victims (English + Native Tamil)
    unknown_accused_regex = (
        r"\b((?:[0-9]+|two|three|four|unknown|unidentified|masked)\s+(?:unknown\s+)?(?:men|persons|individuals|youths|attackers|intruders|riders))\b|"
        r"((?:தெரியாத\s+(?:நபர்கள்|ஆட்கள்|நபர்கள்\s+இருவர்|மர்ம\s+நபர்கள்)|முகமூடி\s+அணிந்த\s+(?:நபர்கள்|இருவர்)))"
    )
    for m in re.finditer(unknown_accused_regex, raw_text, re.IGNORECASE):
        val = m.group(1) or m.group(2)
        if val:
            facts.append({
                "type": "unknown_accused",
                "value": val.strip(),
                "start": m.start(),
                "end": m.end(),
                "source_text": m.group(0),
                "is_certain": True,
                "confidence": 0.92,
                "method": "regex-unknown-accused",
            })

    complainant_names = {f["value"].lower() for f in facts if f["type"] == "complainant"}

    for ent in entities:
        if ent["entity_type"] == "PERSON":
            p_text = ent["entity_text"]
            if p_text.lower() in complainant_names:
                continue

            sent = ent.get("source_sentence", "")
            sent_lower = sent.lower()

            is_accused = any(w in sent_lower for w in [
                "accused", "suspect", "stole", "assaulted", "hit", "attacked", "threatened",
                "took", "demanded", "extorted", "fraud", "cheated", "தாக்கினர்", "திருடினர்", "பறித்தனர்", "மிரட்டினர்"
            ])
            is_witness = any(w in sent_lower for w in [
                "witness", "saw", "present", "bystander", "colleague", "neighbor", "passerby", "சாட்சி", "பார்த்தார்"
            ])
            is_suspicion = any(w in sent_lower for w in [
                "suspect that", "doubt", "believe it might be", "alleged", "allegedly", "சந்தேகம்", "சந்தேகிக்கிறேன்"
            ])

            if is_witness:
                facts.append({
                    "type": "witness",
                    "value": p_text,
                    "start": ent["start"],
                    "end": ent["end"],
                    "source_text": sent,
                    "is_certain": True,
                    "confidence": 0.85,
                    "method": "ner-context-witness",
                })
            else:
                facts.append({
                    "type": "accused" if is_accused else "reported_person",
                    "value": p_text,
                    "start": ent["start"],
                    "end": ent["end"],
                    "source_text": sent,
                    "is_certain": not is_suspicion,
                    "confidence": 0.82,
                    "method": "ner-context-person",
                })

    # C. Dates, Times, Locations
    for ent in entities:
        if ent["entity_type"] == "DATE":
            facts.append({
                "type": "incident_date",
                "value": ent["entity_text"],
                "start": ent["start"],
                "end": ent["end"],
                "source_text": ent.get("source_sentence"),
                "is_certain": True,
                "confidence": 0.90,
                "method": "ner-date",
            })
        elif ent["entity_type"] == "TIME":
            facts.append({
                "type": "incident_time",
                "value": ent["entity_text"],
                "start": ent["start"],
                "end": ent["end"],
                "source_text": ent.get("source_sentence"),
                "is_certain": True,
                "confidence": 0.90,
                "method": "ner-time",
            })
        elif ent["entity_type"] == "LOCATION":
            facts.append({
                "type": "incident_location",
                "value": ent["entity_text"],
                "start": ent["start"],
                "end": ent["end"],
                "source_text": ent.get("source_sentence"),
                "is_certain": True,
                "confidence": 0.88,
                "method": "ner-location",
            })

    # D. Criminal Acts / Offence Predicates (English + Tamil)
    offence_regex = (
        r"\b(assaulted|stabbed|attacked|threatened\s+with|stole|snatched|house-breaking|trespassed|"
        r"cheated|forged|extorted|demanded\s+ransom|hit\s+with|pushed|intercepted|robbed)\b|"
        r"(தாக்கினர்|தாக்கி|திருடினர்|பறித்துச்\s+சென்றனர்|பறித்தனர்|ஏமாற்றினர்|மிரட்டினர்|கொலை\s+மிரட்டல்\s+விடுத்தனர்)"
    )
    for m in re.finditer(offence_regex, raw_text, re.IGNORECASE):
        val = m.group(0)
        facts.append({
            "type": "offence_act",
            "value": val,
            "start": m.start(),
            "end": m.end(),
            "source_text": raw_text[max(0, m.start() - 25): min(len(raw_text), m.end() + 25)],
            "is_certain": True,
            "confidence": 0.90,
            "method": "regex-offence-act",
        })

    # E. Weapons Used (English + Tamil)
    weapon_regex = (
        r"\b(iron\s+rod|knife|sharp\s+object|dagger|gun|pistol|revolver|lathi|wooden\s+stick|blade|firearm|metal\s+pipe)\b|"
        r"(கத்தி|இரும்புத்\s+தடி|துப்பாக்கி|தடி|வாள்|மரக்கட்டை)"
    )
    for m in re.finditer(weapon_regex, raw_text, re.IGNORECASE):
        facts.append({
            "type": "weapon_used",
            "value": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "source_text": raw_text[max(0, m.start() - 20): min(len(raw_text), m.end() + 20)],
            "is_certain": True,
            "confidence": 0.94,
            "method": "regex-weapon",
        })

    # F. Property & Stolen Items (English + Tamil)
    prop_regex = (
        r"\b(gold\s+chain|necklace|wallet|mobile\s+phone|smartphone|iphone|laptop|cash|motorcycle|bike|car|scooter|watch|jewellery|documents|purse)\b|"
        r"(தங்கச்\s+சங்கிலி|தங்க\s+வளையல்|கைபேசி|மடிக்கணினி|பைக்|பணம்|வளையல்|மோதிரம்|பை|நகைகள்)"
    )
    for m in re.finditer(prop_regex, raw_text, re.IGNORECASE):
        facts.append({
            "type": "property",
            "value": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "source_text": raw_text[max(0, m.start() - 20): min(len(raw_text), m.end() + 20)],
            "is_certain": True,
            "confidence": 0.91,
            "method": "regex-property",
        })

    # G. Reported Evidence items (CCTV, receipts, WhatsApp, etc. in English + Tamil)
    evidence_regex = (
        r"\b(cctv(?:\s+footage)?|camera|recording|call\s+records?|phone\s+number|vehicle\s+number|registration\s+plate|receipt|bill|bank\s+statement|whatsapp(?:\s+chat)?|medical\s+certificate|doctor(?:'s)?\s+report)\b|"
        r"(சிசிடிவி(?:\s+பதிவு)?|கேமரா|பதிவு|ரசீது|மருத்துவச்\s+சான்றிதழ்)"
    )
    for m in re.finditer(evidence_regex, raw_text, re.IGNORECASE):
        facts.append({
            "type": "evidence",
            "value": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "source_text": raw_text[max(0, m.start() - 25): min(len(raw_text), m.end() + 25)],
            "is_certain": True,
            "confidence": 0.92,
            "method": "regex-evidence",
        })

    # H. Financial Loss (English + Tamil)
    loss_regex = r"(?:rs\.?|inr|₹|\$|ரூ(?:பாய்|\.)?)\s*([0-9,]+(?:\s*(?:lakh|crore|thousand|ஆயிரம்|லட்சம்))?)"
    for m in re.finditer(loss_regex, raw_text, re.IGNORECASE):
        facts.append({
            "type": "loss",
            "value": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "source_text": m.group(0),
            "is_certain": True,
            "confidence": 0.95,
            "method": "regex-loss",
        })

    # I. Injuries (English + Tamil)
    injury_regex = (
        r"\b(bleeding|fracture|bruise|head\s+injury|wound|stitches|unconscious|admitted\s+to\s+hospital|physical\s+injury)\b|"
        r"(ரத்தக்\s+காயம்|காயம்|எலும்பு\s+முறிவு|மருத்துவமனையில்\s+அனுமதிக்கப்பட்டேன்)"
    )
    for m in re.finditer(injury_regex, raw_text, re.IGNORECASE):
        facts.append({
            "type": "injury",
            "value": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "source_text": raw_text[max(0, m.start() - 25): min(len(raw_text), m.end() + 25)],
            "is_certain": True,
            "confidence": 0.92,
            "method": "regex-injury",
        })

    # J. Completeness check
    if not any(f["type"] == "incident_time" for f in facts):
        facts.append({
            "type": "missing_detail",
            "value": "Exact time of incident is not specified in the complaint.",
            "is_certain": False,
            "confidence": 1.0,
            "method": "system-completeness-check",
        })
    if not any(f["type"] == "incident_location" for f in facts):
        facts.append({
            "type": "missing_detail",
            "value": "Specific location or address of incident is omitted.",
            "is_certain": False,
            "confidence": 1.0,
            "method": "system-completeness-check",
        })

    return facts


def _rule_based_entity_fallback(text: str) -> List[dict]:
    """
    Fallback entity extraction with exact Python character boundaries in raw text.
    Handles English, native Tamil script, and Tamil-English code-mixed complaints.
    Incorporates negative gazetteers and contextual indicators to minimize PERSON false positives.
    """
    entities: List[dict] = []

    # 1. Dates (English & standard numeric)
    date_regex = (
        r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{4})\b"
    )
    for m in re.finditer(date_regex, text, re.IGNORECASE):
        entities.append({
            "entity_text": m.group(0),
            "entity_type": "DATE",
            "start": m.start(),
            "end": m.end(),
            "score": 0.90,
            "source_sentence": text[max(0, m.start() - 25): min(len(text), m.end() + 25)],
            "extraction_method": "regex-date",
        })

    # 2. Times (English & Tamil)
    time_regex = (
        r"\b(?:\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?|\d{1,2}\s*(?:AM|PM|am|pm))\b|"
        r"((?:காலை|மாலை|இரவு|மதியம்)\s*\d{1,2}(?::\d{2})?(?:\s*மணிக்கு)?|\d{1,2}(?::\d{2})?\s*மணிக்கு)"
    )
    for m in re.finditer(time_regex, text):
        entities.append({
            "entity_text": m.group(0),
            "entity_type": "TIME",
            "start": m.start(),
            "end": m.end(),
            "score": 0.90,
            "source_sentence": text[max(0, m.start() - 25): min(len(text), m.end() + 25)],
            "extraction_method": "regex-time",
        })

    # 3. Native Tamil Locations (e.g. சென்னை, பேருந்து நிலையம், etc.)
    tamil_loc_regex = (
        r"([A-Za-z\u0B80-\u0BFA\s]{2,35}?\s+(?:பேருந்து\s+நிலையம்|ரயில்\s+நிலையம்|நகர்|சாலை|தெரு|சந்தை|பூங்கா|அருகே))|"
        r"\b(சென்னை|மதுரை|கோயம்புத்தூர்|திருச்சி|சேலம்|திருநெல்வேலி|ஈரோடு|வேலூர்|திண்டுக்கல்|தஞ்சாவூர்)\b"
    )
    for m in re.finditer(tamil_loc_regex, text):
        raw_val = m.group(0)
        l_strip = len(raw_val) - len(raw_val.lstrip())
        r_strip = len(raw_val) - len(raw_val.rstrip())
        s_off = m.start() + l_strip
        e_off = m.end() - r_strip
        val = text[s_off:e_off]
        if 2 < len(val) < 45:
            entities.append({
                "entity_text": val,
                "entity_type": "LOCATION",
                "start": s_off,
                "end": e_off,
                "score": 0.88,
                "source_sentence": text[max(0, s_off - 25): min(len(text), e_off + 25)],
                "extraction_method": "regex-tamil-location",
            })

    # 4. Native Tamil Person Names (identified by name markers)
    tamil_name_regex = (
        r"(?:என்\s+பெயர்|புகார்தாரர்)\s*[:—\-]?\s*([^\n,.;]+?)(?:\s*ஆகிய|\s*என்பவர்|\.|\n|,|$)|"
        r"(?:எதிரி|குற்றவாளி|தாக்கியவர்)\s*[:—\-]?\s*([^\n,.;]+?)(?:\s*என்பவர்|\.|\n|,|$)|"
        r"(?:சாட்சி)\s*[:—\-]?\s*([^\n,.;]+?)(?:\s*என்பவர்|\.|\n|,|$)"
    )
    for m in re.finditer(tamil_name_regex, text):
        val = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if 2 < len(val) < 40 and not any(k in val for k in ["நிலையம்", "பேருந்து", "காவல்"]):
            span = find_exact_span(text, val, m.start(), m.end())
            if span:
                entities.append({
                    "entity_text": val,
                    "entity_type": "PERSON",
                    "start": span[0],
                    "end": span[1],
                    "score": 0.85,
                    "source_sentence": text[max(0, m.start() - 25): min(len(text), m.end() + 25)],
                    "extraction_method": "regex-tamil-person",
                })

    # 5. English Capitalized Entities (with precision guards against false-positive locations)
    cap_regex = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"
    for m in re.finditer(cap_regex, text):
        val = m.group(0).strip()
        val_lower = val.lower()

        if len(val) <= 2 or val_lower in SKIP_CAP_WORDS:
            continue

        # Check for location cues
        is_loc_indicator = any(loc_ind in val_lower for loc_ind in LOCATION_INDICATORS)
        preceding = text[max(0, m.start() - 10): m.start()].lower()
        is_preceded_by_loc_prep = any(w in preceding for w in ["at ", "in ", "near ", "outside ", "from "])

        if is_loc_indicator or is_preceded_by_loc_prep:
            entities.append({
                "entity_text": val,
                "entity_type": "LOCATION",
                "start": m.start(),
                "end": m.end(),
                "score": 0.85,
                "source_sentence": text[max(0, m.start() - 25): min(len(text), m.end() + 25)],
                "extraction_method": "heuristic-loc",
            })
        else:
            # Person entity candidate
            entities.append({
                "entity_text": val,
                "entity_type": "PERSON",
                "start": m.start(),
                "end": m.end(),
                "score": 0.80,
                "source_sentence": text[max(0, m.start() - 25): min(len(text), m.end() + 25)],
                "extraction_method": "heuristic-person",
            })

    return entities
