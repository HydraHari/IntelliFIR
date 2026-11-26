"""
agent/tools.py — The 6 core Investigation Agent tools for IntelliFIR.
Reuses existing NLP, extraction, validation, legal retrieval, and FAISS similar-case services.
"""
from __future__ import annotations

from datetime import datetime
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.agent.schemas import (
    ComplaintAnalysisInput,
    ComplaintAnalysisOutput,
    EvidenceProvenanceInput,
    EvidenceProvenanceOutput,
    EvidenceSpanItem,
    FactualValidationInput,
    FactualValidationOutput,
    LegalProvisionItem,
    LegalResearchInput,
    LegalResearchOutput,
    SimilarCaseInput,
    SimilarCaseItem,
    SimilarCaseOutput,
    InvestigationReportInput,
    InvestigationReportOutput,
    ToolExecutionRecord,
    ValidationFindingItem,
)
from app.models.complaint import Complaint
from app.models.draft import FIRDraft
from app.models.extraction import EvidenceSpan, ExtractedEntity, ExtractedFact
from app.models.validation import FindingCategory, FindingSeverity, ValidationFinding
from app.services.extraction_service import process_complaint_pipeline
from app.services.legal_service import STATUTORY_PROVISIONS_SEED, search_legal_documents
from app.services.similar_case_service import case_vector_store, search_similar_cases
from app.services.validation_service import run_factual_validation_checks

logger = logging.getLogger(__name__)


def find_complaint_by_identifier(db: Session, identifier: str) -> Optional[Complaint]:
    """Find complaint by UUID or by human-readable reference_id (e.g. CMP-001)."""
    ident = identifier.strip()
    # Try UUID parse first
    try:
        val_uuid = uuid.UUID(ident)
        c = db.query(Complaint).filter(Complaint.id == val_uuid).first()
        if c:
            return c
    except ValueError:
        pass

    # Try reference_id exact match
    c = db.query(Complaint).filter(Complaint.reference_id == ident).first()
    if c:
        return c

    # Try case-insensitive or partial match
    c = db.query(Complaint).filter(Complaint.reference_id.ilike(ident)).first()
    if c:
        return c

    # Try title search fallback
    c = db.query(Complaint).filter(Complaint.title.ilike(f"%{ident}%")).first()
    return c


# ==============================================================================
# TOOL A: COMPLAINT ANALYSIS
# ==============================================================================
class ComplaintAnalysisTool:
    name = "analyze_complaint"
    display_name = "Complaint Analysis"
    description = (
        "Retrieve a complaint by its case ID or reference ID (e.g. CMP-001). "
        "Extracts complainant, accused, victim, date, time, location, property, "
        "amount, weapons, and distinguishes allegations from established facts."
    )

    def execute(self, db: Session, payload: ComplaintAnalysisInput) -> Tuple[ComplaintAnalysisOutput, ToolExecutionRecord]:
        t0 = time.time()
        c = find_complaint_by_identifier(db, payload.case_identifier)
        if not c:
            duration = (time.time() - t0) * 1000
            err_msg = f"Complaint '{payload.case_identifier}' not found in database."
            record = ToolExecutionRecord(
                tool_name=self.name,
                tool_display_name=self.display_name,
                input_arguments=payload.model_dump(),
                output_summary=f"Error: {err_msg}",
                status="failed",
                duration_ms=round(duration, 2),
                error=err_msg,
            )
            raise ValueError(err_msg)

        # Check if structured extraction is already persisted; if not, run pipeline
        facts = db.query(ExtractedFact).filter(ExtractedFact.complaint_id == c.id).all()
        if not facts:
            process_complaint_pipeline(db, c)
            db.refresh(c)
            facts = db.query(ExtractedFact).filter(ExtractedFact.complaint_id == c.id).all()

        raw_text = c.raw_text or c.extracted_text or ""
        complainant: Optional[str] = None
        accused_parties: List[str] = []
        victims: List[str] = []
        witnesses: List[str] = []
        incident_date: Optional[str] = c.incident_date.isoformat() if c.incident_date else None
        incident_time: Optional[str] = None
        incident_location: Optional[str] = c.incident_location
        property_involved: List[str] = []
        amount_involved: Optional[str] = None
        weapons_used: List[str] = []
        established_facts: List[str] = []
        allegations: List[str] = []
        uncertain_details: List[str] = []
        missing_details: List[str] = []

        for f in facts:
            ftype = (f.fact_type or "").lower()
            val = f.fact_value
            is_cert = f.is_certain

            if "complainant" in ftype and not complainant:
                complainant = val
                established_facts.append(f"Complainant identified as: {val}")
            elif "accused" in ftype or "suspect" in ftype:
                if val not in accused_parties:
                    accused_parties.append(val)
                # By criminal law standards, reported accused statements are allegations until proven
                allegations.append(f"Allegation against reported person/accused: {val}")
            elif "victim" in ftype:
                if val not in victims:
                    victims.append(val)
                established_facts.append(f"Victim: {val}")
            elif "witness" in ftype:
                if val not in witnesses:
                    witnesses.append(val)
                established_facts.append(f"Witness: {val}")
            elif "date" in ftype:
                if not incident_date:
                    incident_date = val
                established_facts.append(f"Incident date mentioned: {val}")
            elif "time" in ftype:
                if not incident_time:
                    incident_time = val
                established_facts.append(f"Incident time mentioned: {val}")
            elif "location" in ftype or "place" in ftype:
                if not incident_location:
                    incident_location = val
                established_facts.append(f"Incident location: {val}")
            elif "property" in ftype or "vehicle" in ftype or "item" in ftype:
                if val not in property_involved:
                    property_involved.append(val)
                established_facts.append(f"Property/item involved: {val}")
            elif "amount" in ftype or "money" in ftype:
                if not amount_involved:
                    amount_involved = val
                established_facts.append(f"Financial amount claimed: {val}")
            elif "weapon" in ftype:
                if val not in weapons_used:
                    weapons_used.append(val)
                allegations.append(f"Weapon reported: {val}")
            else:
                if is_cert:
                    established_facts.append(f"{f.fact_type}: {val}")
                else:
                    uncertain_details.append(f"{f.fact_type} (uncertain): {val}")

        # Check if structured_data has additional missing details recorded
        sdata = c.structured_data or {}
        if isinstance(sdata, dict):
            for m in sdata.get("missing_details", []):
                if m not in missing_details:
                    missing_details.append(m)
            for u in sdata.get("uncertain_details", []):
                if u not in uncertain_details:
                    uncertain_details.append(u)

        # Flag missing essential elements
        if not incident_date and "Incident Date" not in missing_details:
            missing_details.append("Specific calendar date of incident")
        if not incident_time and "Incident Time" not in missing_details:
            missing_details.append("Exact or approximate time of incident")
        if not incident_location and "Incident Location" not in missing_details:
            missing_details.append("Specific location / territorial jurisdiction")

        output = ComplaintAnalysisOutput(
            complaint_id=str(c.id),
            reference_id=c.reference_id,
            title=c.title,
            language=c.language or "en",
            raw_text=raw_text,
            complainant=complainant,
            accused_parties=accused_parties,
            victims=victims,
            witnesses=witnesses,
            incident_date=incident_date,
            incident_time=incident_time,
            incident_location=incident_location,
            property_involved=property_involved,
            amount_involved=amount_involved,
            weapons_used=weapons_used,
            established_facts=established_facts,
            allegations=allegations,
            uncertain_details=uncertain_details,
            missing_details=missing_details,
            total_facts_extracted=len(facts),
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments=payload.model_dump(),
            output_summary=(
                f"Successfully parsed case {c.reference_id}: extracted {len(facts)} facts, "
                f"{len(accused_parties)} accused, {len(established_facts)} facts, {len(allegations)} allegations."
            ),
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# ==============================================================================
# TOOL B: EVIDENCE PROVENANCE
# ==============================================================================
class EvidenceProvenanceTool:
    name = "verify_evidence_provenance"
    display_name = "Evidence Provenance"
    description = (
        "Retrieve and strictly verify character-level evidence spans for extracted facts "
        "against the original raw complaint text. Guarantees raw_text[start:end] == span_text, "
        "returning offsets and flagging unsupported facts."
    )

    def execute(self, db: Session, payload: EvidenceProvenanceInput) -> Tuple[EvidenceProvenanceOutput, ToolExecutionRecord]:
        t0 = time.time()
        c = find_complaint_by_identifier(db, payload.case_identifier)
        if not c:
            duration = (time.time() - t0) * 1000
            err_msg = f"Complaint '{payload.case_identifier}' not found."
            record = ToolExecutionRecord(
                tool_name=self.name,
                tool_display_name=self.display_name,
                input_arguments=payload.model_dump(),
                output_summary=f"Error: {err_msg}",
                status="failed",
                duration_ms=round(duration, 2),
                error=err_msg,
            )
            raise ValueError(err_msg)

        raw_text = c.raw_text or c.extracted_text or ""
        spans_db = db.query(EvidenceSpan).filter(EvidenceSpan.complaint_id == c.id).all()
        facts_db = db.query(ExtractedFact).filter(ExtractedFact.complaint_id == c.id).all()

        fact_map = {f.id: f for f in facts_db}
        span_items: List[EvidenceSpanItem] = []
        verified_count = 0
        unsupported_count = 0
        unsupported_facts: List[str] = []
        invariant_preserved = True

        for span in spans_db:
            fact = fact_map.get(span.fact_id)
            fact_type = fact.fact_type if fact else "unknown"
            fact_val = fact.fact_value if fact else span.original_text

            s = span.start_offset
            e = span.end_offset
            orig = span.original_text

            is_valid = False
            error_reason = None

            if 0 <= s < e <= len(raw_text):
                actual_text = raw_text[s:e]
                if actual_text == orig:
                    is_valid = True
                    verified_count += 1
                else:
                    is_valid = False
                    unsupported_count += 1
                    error_reason = f"Mismatch at [{s}:{e}]: expected '{orig}', found '{actual_text}'"
                    unsupported_facts.append(f"{fact_type} ('{fact_val}') - Offset text mismatch")
                    invariant_preserved = False
            else:
                is_valid = False
                unsupported_count += 1
                error_reason = f"Offset bounds error: [{s}:{e}] out of text range (len {len(raw_text)})"
                unsupported_facts.append(f"{fact_type} ('{fact_val}') - Out of range offsets")
                invariant_preserved = False

            span_items.append(
                EvidenceSpanItem(
                    fact_type=fact_type,
                    fact_value=fact_val,
                    start_offset=s,
                    end_offset=e,
                    original_text=orig,
                    verified=is_valid,
                    source_sentence=span.source_sentence,
                    error_reason=error_reason,
                )
            )

        # Check for any facts that have NO evidence span
        spanned_fact_ids = {s.fact_id for s in spans_db}
        for f in facts_db:
            if f.id not in spanned_fact_ids:
                unsupported_count += 1
                unsupported_facts.append(f"{f.fact_type} ('{f.fact_value}') - No source evidence span recorded")

        output = EvidenceProvenanceOutput(
            total_facts_checked=len(facts_db),
            verified_count=verified_count,
            unsupported_count=unsupported_count,
            spans=span_items,
            unsupported_facts=unsupported_facts,
            provenance_invariant_preserved=invariant_preserved,
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments=payload.model_dump(),
            output_summary=(
                f"Verified {verified_count}/{len(facts_db)} facts with strict character offsets. "
                f"Unsupported: {unsupported_count}. Invariant preserved: {invariant_preserved}."
            ),
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# ==============================================================================
# TOOL C: FACTUAL VALIDATION
# ==============================================================================
class FactualValidationTool:
    name = "validate_complaint_facts"
    display_name = "Factual Validation"
    description = (
        "Compare complaint and draft claims to detect unsupported statements, contradictions, "
        "timeline inconsistencies, and missing statutory elements. Returns structured findings."
    )

    def execute(self, db: Session, payload: FactualValidationInput) -> Tuple[FactualValidationOutput, ToolExecutionRecord]:
        t0 = time.time()
        raw_text = payload.raw_complaint or ""
        clean_draft = payload.draft_or_claims or ""

        # If case_identifier provided and raw_complaint not passed, fetch from DB
        if payload.case_identifier and not raw_text:
            c = find_complaint_by_identifier(db, payload.case_identifier)
            if c:
                raw_text = c.raw_text or c.extracted_text or ""
                # If no draft supplied, check if draft exists in DB
                if not clean_draft:
                    d = db.query(FIRDraft).filter(FIRDraft.complaint_id == c.id).order_by(FIRDraft.created_at.desc()).first()
                    if d:
                        clean_draft = d.draft_text or ""

        if not raw_text.strip():
            duration = (time.time() - t0) * 1000
            err_msg = "No complaint text provided or found for factual validation."
            record = ToolExecutionRecord(
                tool_name=self.name,
                tool_display_name=self.display_name,
                input_arguments=payload.model_dump(),
                output_summary=f"Error: {err_msg}",
                status="failed",
                duration_ms=round(duration, 2),
                error=err_msg,
            )
            raise ValueError(err_msg)

        # Run decoupled pure validation check
        raw_findings = run_factual_validation_checks(
            raw_complaint=raw_text,
            clean_draft=clean_draft or raw_text,
        )

        contradictions: List[ValidationFindingItem] = []
        timeline_inconsistencies: List[ValidationFindingItem] = []
        missing_statutory_elements: List[ValidationFindingItem] = []
        ambiguities: List[ValidationFindingItem] = []
        unsupported_claims: List[ValidationFindingItem] = []
        all_findings: List[ValidationFindingItem] = []

        for idx, f in enumerate(raw_findings, start=1):
            cat = str(f.get("category", "")).lower()
            if hasattr(f.get("category"), "value"):
                cat = str(f["category"].value).lower()

            sev = str(f.get("severity", "")).lower()
            if hasattr(f.get("severity"), "value"):
                sev = str(f["severity"].value).lower()

            item = ValidationFindingItem(
                finding_id=f.get("finding_id", f"VF-{idx:03d}"),
                category=cat,
                claim_or_statement=f.get("draft_claim", "Complaint Statement"),
                explanation=f.get("explanation", ""),
                severity=sev,
                suggested_action=f.get("suggested_action", ""),
                source_evidence=f.get("source_evidence"),
            )
            all_findings.append(item)

            if "contradiction" in cat:
                contradictions.append(item)
            elif "timeline" in cat:
                timeline_inconsistencies.append(item)
            elif "missing" in cat:
                missing_statutory_elements.append(item)
            elif "ambiguity" in cat or "uncertainty" in cat:
                ambiguities.append(item)
            elif "unsupported" in cat:
                unsupported_claims.append(item)

        output = FactualValidationOutput(
            total_findings=len(all_findings),
            contradictions=contradictions,
            timeline_inconsistencies=timeline_inconsistencies,
            missing_statutory_elements=missing_statutory_elements,
            ambiguities=ambiguities,
            unsupported_claims=unsupported_claims,
            all_findings=all_findings,
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments=payload.model_dump(),
            output_summary=(
                f"Found {len(all_findings)} items: {len(contradictions)} contradictions, "
                f"{len(missing_statutory_elements)} missing statutory elements, "
                f"{len(unsupported_claims)} unsupported claims, {len(ambiguities)} ambiguities."
            ),
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# ==============================================================================
# TOOL D: LEGAL RESEARCH
# ==============================================================================
class LegalResearchTool:
    name = "research_legal_provisions"
    display_name = "Legal Research"
    description = (
        "Search the verified legal document database for Bharatiya Nyaya Sanhita (BNS 2023), "
        "BNSS, BSA, and IPC correspondences. Returns source passages, citations, and classification. "
        "Strictly grounded — never invents statutory sections."
    )

    def execute(self, db: Session, payload: LegalResearchInput) -> Tuple[LegalResearchOutput, ToolExecutionRecord]:
        t0 = time.time()
        query = payload.query.strip()
        top_k = payload.top_k or 4

        # 1. Search vector database
        results = search_legal_documents(db, query=query, top_k=top_k, threshold=payload.min_score)

        # 2. Also perform keyword & section matching across STATUTORY_PROVISIONS_SEED
        # to ensure critical sections (e.g. 303, 304, 318, 115, 309, 329) are never missed
        seed_matches: List[Dict[str, Any]] = []
        tokens = set(re.findall(r"\w+", query.lower()))

        for seed in STATUTORY_PROVISIONS_SEED:
            text_corpus = (
                f"{seed.get('title', '')} {seed.get('content', '')} {seed.get('source', '')} "
                f"{str(seed.get('metadata', ''))}"
            ).lower()

            # Score based on token overlap
            match_score = 0.0
            for tok in tokens:
                if len(tok) >= 3 and tok in text_corpus:
                    match_score += 0.25

            # If specific section mentioned like "303" or "379"
            for seed_sec in ["303", "304", "318", "115", "309", "329", "420", "379"]:
                if seed_sec in tokens and seed_sec in text_corpus:
                    match_score += 0.50

            if match_score > 0.3:
                seed_matches.append({
                    "title": seed.get("title"),
                    "source": seed.get("source"),
                    "content": seed.get("content"),
                    "provision_type": seed.get("provision_type", "statute"),
                    "score": min(round(match_score, 4), 0.99),
                    "metadata": seed.get("metadata", {}),
                })

        # Combine vector results and keyword matches, deduplicating by title
        combined_by_title: Dict[str, Dict[str, Any]] = {}
        for r in results:
            t = r.get("title", "")
            if t:
                combined_by_title[t] = r

        for sm in seed_matches:
            t = sm.get("title", "")
            if t not in combined_by_title:
                combined_by_title[t] = sm

        provisions: List[LegalProvisionItem] = []
        citations: List[str] = []

        for item in list(combined_by_title.values())[:top_k]:
            meta = item.get("metadata", {})
            title = item.get("title", "Statutory Provision")
            prov = LegalProvisionItem(
                title=title,
                source=item.get("source", "Bharatiya Nyaya Sanhita, 2023"),
                provision_type=item.get("provision_type", "statute"),
                content=item.get("content", ""),
                score=item.get("score"),
                ipc_counterpart=meta.get("ipc_counterpart"),
                bns_section=meta.get("bns_section"),
                cognizable=meta.get("cognizable"),
                bailable=meta.get("bailable"),
            )
            provisions.append(prov)
            citations.append(f"{prov.title} [{prov.source}]")

        notes = (
            "Legal provisions referenced are strictly from the verified statutory corpus (BNS 2023 / IPC 1860). "
            "Under the Bharatiya Nyaya Sanhita (w.e.f. July 1, 2024), new numerical sections supersede historical IPC sections, "
            "with IPC correspondence retained for transitional investigation continuity."
        )

        output = LegalResearchOutput(
            query=query,
            provisions=provisions,
            citations=citations,
            statutory_notes=notes,
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments=payload.model_dump(),
            output_summary=f"Retrieved {len(provisions)} verified legal provisions for query '{query}'.",
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# ==============================================================================
# TOOL E: SIMILAR CASE RETRIEVAL
# ==============================================================================
class SimilarCaseTool:
    name = "retrieve_similar_cases"
    display_name = "Similar Case Retrieval"
    description = (
        "Query the FAISS vector database to retrieve semantically related previous cases. "
        "Returns case metadata and similarity scores. Strictly notes that similarity does not establish guilt."
    )

    def execute(self, db: Session, payload: SimilarCaseInput) -> Tuple[SimilarCaseOutput, ToolExecutionRecord]:
        t0 = time.time()
        query = payload.query_text.strip()
        top_k = payload.top_k or 4

        try:
            matches = search_similar_cases(db, query_text=query, top_k=top_k, threshold=payload.threshold)
        except Exception as exc:
            logger.warning("FAISS similar cases search failed: %s", exc)
            matches = []

        case_items: List[SimilarCaseItem] = []
        for m in matches:
            ref = m.get("reference_id") or m.get("id", "CASE-REF")
            summary = m.get("summary") or m.get("content", "")
            cat = m.get("category")
            score = float(m.get("score", 0.0))
            meta = m.get("metadata", {})
            case_items.append(
                SimilarCaseItem(
                    reference_id=str(ref),
                    summary=summary,
                    category=cat,
                    score=round(score, 4),
                    metadata=meta,
                )
            )

        output = SimilarCaseOutput(
            query=query,
            cases=case_items,
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments=payload.model_dump(),
            output_summary=(
                f"Retrieved {len(case_items)} similar cases from vector index. "
                f"Legal disclaimer attached."
            ),
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# ==============================================================================
# TOOL F: INVESTIGATION REPORT GENERATOR
# ==============================================================================
class InvestigationReportTool:
    name = "generate_investigation_report"
    display_name = "Investigation Report Generator"
    description = (
        "Combine verified facts, evidence provenance spans, factual validation findings, "
        "applicable legal sections, and precedent cases into a structured investigation report."
    )

    def execute(self, payload: InvestigationReportInput) -> Tuple[InvestigationReportOutput, ToolExecutionRecord]:
        t0 = time.time()
        analysis = payload.analysis
        provenance = payload.provenance
        validation = payload.validation
        legal = payload.legal_provisions
        similar = payload.similar_cases

        case_id = payload.case_identifier or (analysis.reference_id if analysis else "CMP-GENERAL")
        title = f"INVESTIGATION SUPPORT REPORT: Case {case_id}"

        # 1. Executive Summary
        complainant_str = analysis.complainant if (analysis and analysis.complainant) else "Unknown/Unstated Complainant"
        accused_str = ", ".join(analysis.accused_parties) if (analysis and analysis.accused_parties) else "Unidentified / Unknown Person(s)"
        loc_str = analysis.incident_location if (analysis and analysis.incident_location) else "Unspecified Jurisdiction"
        date_str = analysis.incident_date if (analysis and analysis.incident_date) else "Unspecified Date"

        exec_summary = (
            f"Preliminary investigation assessment for Complaint Docket {case_id}. "
            f"Lodged by {complainant_str} regarding an incident on or around {date_str} at {loc_str}. "
            f"Reported suspect(s)/accused: {accused_str}."
        )

        # 2. Parties Involved
        parties = {
            "complainant": complainant_str,
            "reported_accused": analysis.accused_parties if analysis else [],
            "victims": analysis.victims if analysis else [],
            "witnesses": analysis.witnesses if analysis else [],
        }

        # 3. Established Facts vs Allegations
        established_facts: List[str] = []
        allegations_and_uncertainties: List[str] = []

        if analysis:
            established_facts.extend(analysis.established_facts)
            allegations_and_uncertainties.extend(analysis.allegations)
            for u in analysis.uncertain_details:
                allegations_and_uncertainties.append(f"[UNCERTAINTY] {u}")
        else:
            established_facts.append("No automated fact extraction performed.")

        # 4. Evidence Provenance Summary
        if provenance:
            prov_summary = (
                f"Total facts verified with character offsets: {provenance.verified_count}/{provenance.total_facts_checked}. "
                f"Unsupported facts: {provenance.unsupported_count}. "
                f"Character-level invariant preserved: {provenance.provenance_invariant_preserved}."
            )
        else:
            prov_summary = "Character-level evidence provenance was not independently executed."

        # 5. Contradictions & Gaps
        contradictions_and_gaps: List[str] = []
        if validation:
            for c in validation.contradictions:
                contradictions_and_gaps.append(f"CONTRADICTION: {c.explanation} (Severity: {c.severity})")
            for m in validation.missing_statutory_elements:
                contradictions_and_gaps.append(f"MISSING ELEMENT: {c.claim_or_statement if 'c' in locals() else m.claim_or_statement} - {m.explanation}")
            for u in validation.unsupported_claims:
                contradictions_and_gaps.append(f"UNSUPPORTED STATEMENT: {u.claim_or_statement} - {u.explanation}")
            for a in validation.ambiguities:
                contradictions_and_gaps.append(f"AMBIGUOUS DETAIL: {a.claim_or_statement} - {a.explanation}")
        if analysis:
            for mis in analysis.missing_details:
                gap_item = f"MISSING INQUIRY: {mis}"
                if gap_item not in contradictions_and_gaps:
                    contradictions_and_gaps.append(gap_item)

        if not contradictions_and_gaps:
            contradictions_and_gaps.append("No fatal statutory omissions or contradictions identified in preliminary check.")

        # 6. Applicable Legal Framework
        applicable_legal: List[str] = []
        if legal and legal.provisions:
            for p in legal.provisions:
                bns_text = f"• {p.title} ({p.source})"
                if p.ipc_counterpart:
                    bns_text += f" [Historical Counterpart: {p.ipc_counterpart}]"
                if p.cognizable is not None:
                    bns_text += f" — {'Cognizable' if p.cognizable else 'Non-Cognizable'}, {'Bailable' if p.bailable else 'Non-Bailable'}"
                applicable_legal.append(bns_text)
        else:
            applicable_legal.append("No specific statutory sections matched yet.")

        # 7. Suggested Investigator Actions & Questions
        suggested_actions: List[str] = []
        if analysis and analysis.accused_parties:
            suggested_actions.append(f"Examine CCTV or CDR records corresponding to reported accused: {', '.join(analysis.accused_parties)}")
        if analysis and not analysis.incident_time:
            suggested_actions.append("Directly interview complainant to establish exact or approximate timeframe of incident.")
        if analysis and not analysis.incident_location:
            suggested_actions.append("Obtain territorial coordinates and site map to confirm police station jurisdictional bounds.")
        if analysis and analysis.property_involved:
            suggested_actions.append(f"Collect purchase invoice, serial numbers, or IMEI for reported property: {', '.join(analysis.property_involved)}")
        if validation:
            for item in validation.all_findings:
                if item.suggested_action and item.suggested_action not in suggested_actions:
                    suggested_actions.append(item.suggested_action)

        if not suggested_actions:
            suggested_actions.append("Issue Section 91 BNSS notice for document / electronic evidence preservation.")

        # Format complete Markdown
        md_lines = [
            f"# {title}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | **Docket:** {case_id}",
            "---",
            "## 1. Executive Summary",
            exec_summary,
            "",
            "## 2. Key Parties Involved",
            f"- **Complainant:** {parties['complainant']}",
            f"- **Reported Accused/Suspects:** {', '.join(parties['reported_accused']) if parties['reported_accused'] else 'None reported'}",
            f"- **Victim(s):** {', '.join(parties['victims']) if parties['victims'] else 'Complainant or Unspecified'}",
            f"- **Witnesses:** {', '.join(parties['witnesses']) if parties['witnesses'] else 'None mentioned'}",
            "",
            "## 3. Established Facts vs. Unsubstantiated Allegations",
            "### Verified Complaint Facts:",
        ]
        for f in established_facts:
            md_lines.append(f"- {f}")

        md_lines.extend([
            "",
            "### Unsubstantiated Allegations & Uncertain Details:",
        ])
        for a in (allegations_and_uncertainties or ["None recorded"]):
            md_lines.append(f"- {a}")

        md_lines.extend([
            "",
            "## 4. Evidence Provenance & Verification Audit",
            prov_summary,
            "",
            "## 5. Inconsistencies, Contradictions & Information Gaps",
        ])
        for g in contradictions_and_gaps:
            md_lines.append(f"- {g}")

        md_lines.extend([
            "",
            "## 6. Applicable Statutory Framework (BNS 2023 / BNSS 2023)",
        ])
        for l in applicable_legal:
            md_lines.append(l)

        if similar and similar.cases:
            md_lines.extend([
                "",
                "## 7. Similar Case References & Modus Operandi Precedents",
                f"> *{similar.disclaimer}*",
            ])
            for sc in similar.cases:
                md_lines.append(f"- **{sc.reference_id}** (Similarity: {sc.score}): {sc.summary}")

        md_lines.extend([
            "",
            "## 8. Suggested Follow-Up Actions for Investigating Officer",
        ])
        for act in suggested_actions:
            md_lines.append(f"1. {act}")

        md_lines.extend([
            "",
            "---",
            "### Statutory Regulatory Notice",
            "> **HUMAN-IN-THE-LOOP MANDATE:** This document is an AI-generated investigation support summary. "
            "It does NOT constitute an officially registered FIR or judicial determination of guilt. "
            "All recommendations, section endorsements, and verification conclusions must be formally approved "
            "by the Investigating Officer in accordance with the Bharatiya Nagarik Suraksha Sanhita (BNSS 2023).",
        ])

        formatted_md = "\n".join(md_lines)

        output = InvestigationReportOutput(
            case_identifier=case_id,
            title=title,
            executive_summary=exec_summary,
            parties_involved=parties,
            established_facts=established_facts,
            allegations_and_uncertainties=allegations_and_uncertainties,
            evidence_provenance_summary=prov_summary,
            contradictions_and_gaps=contradictions_and_gaps,
            applicable_legal_framework=applicable_legal,
            suggested_investigator_actions=suggested_actions,
            formatted_markdown=formatted_md,
        )

        duration = (time.time() - t0) * 1000
        record = ToolExecutionRecord(
            tool_name=self.name,
            tool_display_name=self.display_name,
            input_arguments={"case_identifier": case_id},
            output_summary=f"Synthesized comprehensive investigation report ({len(formatted_md)} characters).",
            status="success",
            duration_ms=round(duration, 2),
        )
        return output, record


# Instantiate tool singletons
complaint_analysis_tool = ComplaintAnalysisTool()
evidence_provenance_tool = EvidenceProvenanceTool()
factual_validation_tool = FactualValidationTool()
legal_research_tool = LegalResearchTool()
similar_case_tool = SimilarCaseTool()
investigation_report_tool = InvestigationReportTool()
