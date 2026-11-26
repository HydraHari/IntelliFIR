"""
agent/schemas.py — Pydantic schemas for the IntelliFIR AI Investigation Agent.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Tool Execution Records
# ------------------------------------------------------------------------------
class ToolExecutionRecord(BaseModel):
    tool_name: str
    tool_display_name: str
    input_arguments: Dict[str, Any]
    output_summary: str
    status: str = Field(..., description="'success' | 'failed' | 'skipped'")
    duration_ms: float
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ------------------------------------------------------------------------------
# Tool A: Complaint Analysis Schemas
# ------------------------------------------------------------------------------
class ComplaintAnalysisInput(BaseModel):
    case_identifier: str = Field(..., description="Complaint UUID or reference ID (e.g. CMP-001)")


class FactItem(BaseModel):
    type: str
    value: str
    is_certain: bool = True
    confidence: float = 0.9
    source_span: Optional[Tuple[int, int]] = None
    source_text: Optional[str] = None


class ComplaintAnalysisOutput(BaseModel):
    complaint_id: str
    reference_id: str
    title: str
    language: str
    raw_text: str
    complainant: Optional[str] = None
    accused_parties: List[str] = Field(default_factory=list)
    victims: List[str] = Field(default_factory=list)
    witnesses: List[str] = Field(default_factory=list)
    incident_date: Optional[str] = None
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    property_involved: List[str] = Field(default_factory=list)
    amount_involved: Optional[str] = None
    weapons_used: List[str] = Field(default_factory=list)
    established_facts: List[str] = Field(default_factory=list)
    allegations: List[str] = Field(default_factory=list)
    uncertain_details: List[str] = Field(default_factory=list)
    missing_details: List[str] = Field(default_factory=list)
    total_facts_extracted: int = 0


# ------------------------------------------------------------------------------
# Tool B: Evidence Provenance Schemas
# ------------------------------------------------------------------------------
class EvidenceProvenanceInput(BaseModel):
    case_identifier: str = Field(..., description="Complaint UUID or reference ID")
    extracted_facts: Optional[List[Dict[str, Any]]] = None


class EvidenceSpanItem(BaseModel):
    fact_type: str
    fact_value: str
    start_offset: int
    end_offset: int
    original_text: str
    verified: bool
    source_sentence: Optional[str] = None
    error_reason: Optional[str] = None


class EvidenceProvenanceOutput(BaseModel):
    total_facts_checked: int = 0
    verified_count: int = 0
    unsupported_count: int = 0
    spans: List[EvidenceSpanItem] = Field(default_factory=list)
    unsupported_facts: List[str] = Field(default_factory=list)
    provenance_invariant_preserved: bool = True


# ------------------------------------------------------------------------------
# Tool C: Factual Validation Schemas
# ------------------------------------------------------------------------------
class FactualValidationInput(BaseModel):
    case_identifier: Optional[str] = None
    raw_complaint: Optional[str] = None
    draft_or_claims: Optional[str] = None


class ValidationFindingItem(BaseModel):
    finding_id: str
    category: str
    claim_or_statement: str
    explanation: str
    severity: str
    suggested_action: str
    source_evidence: Optional[str] = None


class FactualValidationOutput(BaseModel):
    total_findings: int = 0
    contradictions: List[ValidationFindingItem] = Field(default_factory=list)
    timeline_inconsistencies: List[ValidationFindingItem] = Field(default_factory=list)
    missing_statutory_elements: List[ValidationFindingItem] = Field(default_factory=list)
    ambiguities: List[ValidationFindingItem] = Field(default_factory=list)
    unsupported_claims: List[ValidationFindingItem] = Field(default_factory=list)
    all_findings: List[ValidationFindingItem] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Tool D: Legal Research Schemas
# ------------------------------------------------------------------------------
class LegalResearchInput(BaseModel):
    query: str = Field(..., description="Search query describing offence, acts, or specific sections")
    top_k: int = 4
    min_score: float = 0.20


class LegalProvisionItem(BaseModel):
    title: str
    source: str
    provision_type: str
    content: str
    score: Optional[float] = None
    ipc_counterpart: Optional[str] = None
    bns_section: Optional[str] = None
    cognizable: Optional[bool] = None
    bailable: Optional[bool] = None


class LegalResearchOutput(BaseModel):
    query: str
    provisions: List[LegalProvisionItem] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    statutory_notes: str = ""


# ------------------------------------------------------------------------------
# Tool E: Similar Case Retrieval Schemas
# ------------------------------------------------------------------------------
class SimilarCaseInput(BaseModel):
    query_text: str = Field(..., description="Factual or narrative text of the case")
    top_k: int = 4
    threshold: Optional[float] = None


class SimilarCaseItem(BaseModel):
    reference_id: str
    summary: str
    category: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimilarCaseOutput(BaseModel):
    query: str
    cases: List[SimilarCaseItem] = Field(default_factory=list)
    disclaimer: str = (
        "LEGAL ADVISORY NOTICE: Semantically similar cases are retrieved solely as investigation reference "
        "and investigative context. Factual or linguistic similarity does not establish legal equivalence, "
        "judicial precedent, or liability. Independent verification of statutory ingredients is mandatory."
    )


# ------------------------------------------------------------------------------
# Tool F: Investigation Report Generator Schemas
# ------------------------------------------------------------------------------
class InvestigationReportInput(BaseModel):
    case_identifier: Optional[str] = None
    analysis: Optional[ComplaintAnalysisOutput] = None
    provenance: Optional[EvidenceProvenanceOutput] = None
    validation: Optional[FactualValidationOutput] = None
    legal_provisions: Optional[LegalResearchOutput] = None
    similar_cases: Optional[SimilarCaseOutput] = None
    custom_investigator_notes: Optional[str] = None


class InvestigationReportOutput(BaseModel):
    report_id: str = Field(default_factory=lambda: f"IR-{uuid.uuid4().hex[:6].upper()}")
    case_identifier: Optional[str] = None
    title: str
    executive_summary: str
    parties_involved: Dict[str, Any] = Field(default_factory=dict)
    established_facts: List[str] = Field(default_factory=list)
    allegations_and_uncertainties: List[str] = Field(default_factory=list)
    evidence_provenance_summary: str
    contradictions_and_gaps: List[str] = Field(default_factory=list)
    applicable_legal_framework: List[str] = Field(default_factory=list)
    suggested_investigator_actions: List[str] = Field(default_factory=list)
    human_review_notice: str = (
        "HUMAN-IN-THE-LOOP MANDATE: This investigation report is generated by IntelliFIR's evidence-grounded AI "
        "as an investigative aid. Official FIR registration, charge framing, and criminal culpability decisions "
        "remain exclusively within the authority of the Investigating Officer and Station House Officer."
    )
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    formatted_markdown: str = ""


# ------------------------------------------------------------------------------
# API Agent Request / Response Schemas
# ------------------------------------------------------------------------------
class AgentRunRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000, description="Investigator query or directive")
    complaint_id: Optional[str] = Field(None, description="Complaint UUID or reference_id (e.g. CMP-001)")
    conversation_id: Optional[str] = Field(None, description="Conversation session ID")
    tools_allowed: Optional[List[str]] = Field(None, description="Explicit tool restriction if any")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Recent conversation turns")


class AgentRunResponse(BaseModel):
    conversation_id: str
    answer: str
    execution_status: str = Field(..., description="'completed' | 'partial' | 'failed' | 'action_blocked'")
    intent: str
    selected_tools: List[str] = Field(default_factory=list)
    tool_executions: List[ToolExecutionRecord] = Field(default_factory=list)
    complaint_analysis: Optional[ComplaintAnalysisOutput] = None
    evidence_provenance: Optional[EvidenceProvenanceOutput] = None
    factual_validation: Optional[FactualValidationOutput] = None
    legal_research: Optional[LegalResearchOutput] = None
    similar_cases: Optional[SimilarCaseOutput] = None
    investigation_report: Optional[InvestigationReportOutput] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    approval_message: Optional[str] = None
    is_retrieval_only: bool = False
