"""
agent/orchestrator.py — Multi-step autonomous Investigation Agent orchestrator.
Handles intent decomposition, dynamic tool selection, execution graph state,
error recovery, human-in-the-loop protection, and grounded response synthesis.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy.orm import Session

from app.agent.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    ComplaintAnalysisInput,
    ComplaintAnalysisOutput,
    EvidenceProvenanceInput,
    EvidenceProvenanceOutput,
    FactualValidationInput,
    FactualValidationOutput,
    InvestigationReportInput,
    InvestigationReportOutput,
    LegalResearchInput,
    LegalResearchOutput,
    SimilarCaseInput,
    SimilarCaseOutput,
    ToolExecutionRecord,
)
from app.agent.tools import (
    complaint_analysis_tool,
    evidence_provenance_tool,
    factual_validation_tool,
    find_complaint_by_identifier,
    investigation_report_tool,
    legal_research_tool,
    similar_case_tool,
)
from app.ml.llm.ollama_provider import ollama_provider
from app.models.complaint import Complaint

logger = logging.getLogger(__name__)

CONSEQUENTIAL_PATTERNS = [
    r"\b(register|file|submit)\s+(the\s+)?(official\s+)?fir\b",
    r"\b(arrest|detain|jail)\s+(the\s+)?accused\b",
    r"\b(declare|rule|pronounce)\s+.*?(guilty|innocent)\b",
    r"\b(convict|sentence)\b",
    r"\b(delete|drop|destroy)\s+(the\s+)?(case|complaint|evidence)\b",
]


class InvestigationAgentOrchestrator:
    """
    Central AI Investigation Agent Orchestrator.
    Executes multi-step workflows, manages state, routes conditionally,
    and enforces human-in-the-loop controls.
    """

    def __init__(self, max_steps: int = 6):
        self.max_steps = max_steps

    def execute(self, db: Session, request: AgentRunRequest) -> AgentRunResponse:
        t_start = time.time()
        conv_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
        user_message = request.message.strip()

        # ----------------------------------------------------------------------
        # 1. Safety Guardrail: Check for consequential actions
        # ----------------------------------------------------------------------
        is_consequential, block_reason = self._check_consequential_action(user_message)
        if is_consequential:
            return AgentRunResponse(
                conversation_id=conv_id,
                answer=(
                    f"⚠️ **ACTION BLOCKED BY STATUTORY SAFETY CONTROLS**\n\n"
                    f"{block_reason}\n\n"
                    f"> **Statutory Notice:** Under Bharatiya Nagarik Suraksha Sanhita (BNSS 2023), "
                    f"substantive criminal proceedings (FIR registration, arrest warrants, case closure) "
                    f"cannot be autonomously executed by AI. They require verified manual authorisation "
                    f"by a competent Investigating Officer (IO) or Station House Officer (SHO)."
                ),
                execution_status="action_blocked",
                intent="consequential_action_attempt",
                selected_tools=[],
                tool_executions=[],
                requires_human_approval=True,
                approval_message=block_reason,
                follow_up_questions=[
                    "Would you like me to prepare an FIR draft for your official manual review?",
                    "Should I identify missing statutory elements before you proceed?",
                ],
            )

        # ----------------------------------------------------------------------
        # 2. Extract Target Case Identifier
        # ----------------------------------------------------------------------
        case_id = self._extract_case_identifier(user_message, request.complaint_id)

        # ----------------------------------------------------------------------
        # 3. Intent Understanding & Dynamic Tool Selection
        # ----------------------------------------------------------------------
        intent, planned_tools = self._plan_workflow(user_message, case_id, request.tools_allowed)

        # ----------------------------------------------------------------------
        # 4. Multi-Step Workflow Execution
        # ----------------------------------------------------------------------
        tool_records: List[ToolExecutionRecord] = []
        analysis_res: Optional[ComplaintAnalysisOutput] = None
        provenance_res: Optional[EvidenceProvenanceOutput] = None
        validation_res: Optional[FactualValidationOutput] = None
        legal_res: Optional[LegalResearchOutput] = None
        similar_res: Optional[SimilarCaseOutput] = None
        report_res: Optional[InvestigationReportOutput] = None

        step_count = 0
        execution_status = "completed"

        # Check if case was requested but does not exist in DB
        complaint_obj: Optional[Complaint] = None
        if case_id:
            complaint_obj = find_complaint_by_identifier(db, case_id)
            if not complaint_obj and ("analyze_complaint" in planned_tools or "verify_evidence_provenance" in planned_tools):
                err_msg = f"Complaint docket '{case_id}' could not be located in the system database."
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name="complaint_lookup",
                        tool_display_name="Complaint Lookup",
                        input_arguments={"case_identifier": case_id},
                        output_summary=f"Failed: {err_msg}",
                        status="failed",
                        duration_ms=5.0,
                        error=err_msg,
                    )
                )
                return AgentRunResponse(
                    conversation_id=conv_id,
                    answer=(
                        f"❌ **Case Not Found:** I could not locate any complaint matching `{case_id}` in the records.\n\n"
                        f"Please verify the case reference ID (e.g. `CMP-001`, `CMP-XXXXXX`) or select an active case "
                        f"from the Complaint Docket list to proceed with the investigation workflow."
                    ),
                    execution_status="failed",
                    intent=intent,
                    selected_tools=planned_tools,
                    tool_executions=tool_records,
                    follow_up_questions=[
                        "Would you like to list the most recently lodged complaints?",
                        "Can you provide the complainant's name or incident location to locate the docket?",
                    ],
                )

        # Step A: Complaint Analysis
        if "analyze_complaint" in planned_tools and step_count < self.max_steps:
            step_count += 1
            try:
                analysis_res, rec = complaint_analysis_tool.execute(
                    db, ComplaintAnalysisInput(case_identifier=case_id or "")
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (analyze_complaint): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=complaint_analysis_tool.name,
                        tool_display_name=complaint_analysis_tool.display_name,
                        input_arguments={"case_identifier": case_id},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # Step B: Evidence Provenance
        if "verify_evidence_provenance" in planned_tools and step_count < self.max_steps:
            step_count += 1
            try:
                provenance_res, rec = evidence_provenance_tool.execute(
                    db, EvidenceProvenanceInput(case_identifier=case_id or "")
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (verify_evidence_provenance): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=evidence_provenance_tool.name,
                        tool_display_name=evidence_provenance_tool.display_name,
                        input_arguments={"case_identifier": case_id},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # Step C: Factual Validation
        if "validate_complaint_facts" in planned_tools and step_count < self.max_steps:
            step_count += 1
            try:
                raw_c_text = complaint_obj.raw_text or complaint_obj.extracted_text if complaint_obj else None
                validation_res, rec = factual_validation_tool.execute(
                    db,
                    FactualValidationInput(
                        case_identifier=case_id,
                        raw_complaint=raw_c_text or (analysis_res.raw_text if analysis_res else user_message),
                    ),
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (validate_complaint_facts): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=factual_validation_tool.name,
                        tool_display_name=factual_validation_tool.display_name,
                        input_arguments={"case_identifier": case_id},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # Step D: Legal Research
        if "research_legal_provisions" in planned_tools and step_count < self.max_steps:
            step_count += 1
            # Build search query
            legal_query = self._build_legal_query(user_message, analysis_res)
            try:
                legal_res, rec = legal_research_tool.execute(
                    db, LegalResearchInput(query=legal_query, top_k=4)
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (research_legal_provisions): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=legal_research_tool.name,
                        tool_display_name=legal_research_tool.display_name,
                        input_arguments={"query": legal_query},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # Step E: Similar Case Retrieval
        if "retrieve_similar_cases" in planned_tools and step_count < self.max_steps:
            step_count += 1
            similar_query = self._build_similar_case_query(user_message, analysis_res)
            try:
                similar_res, rec = similar_case_tool.execute(
                    db, SimilarCaseInput(query_text=similar_query, top_k=3)
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (retrieve_similar_cases): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=similar_case_tool.name,
                        tool_display_name=similar_case_tool.display_name,
                        input_arguments={"query_text": similar_query},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # Step F: Investigation Report Generator
        if "generate_investigation_report" in planned_tools and step_count < self.max_steps:
            step_count += 1
            try:
                report_res, rec = investigation_report_tool.execute(
                    InvestigationReportInput(
                        case_identifier=case_id,
                        analysis=analysis_res,
                        provenance=provenance_res,
                        validation=validation_res,
                        legal_provisions=legal_res,
                        similar_cases=similar_res,
                    )
                )
                tool_records.append(rec)
            except Exception as exc:
                logger.error("Tool execution failed (generate_investigation_report): %s", exc)
                execution_status = "partial"
                tool_records.append(
                    ToolExecutionRecord(
                        tool_name=investigation_report_tool.name,
                        tool_display_name=investigation_report_tool.display_name,
                        input_arguments={"case_identifier": case_id},
                        output_summary=f"Execution error: {exc}",
                        status="failed",
                        duration_ms=10.0,
                        error=str(exc),
                    )
                )

        # ----------------------------------------------------------------------
        # 5. Formulate Evidence-Grounded Final Response
        # ----------------------------------------------------------------------
        answer = self._synthesize_answer(
            user_message=user_message,
            intent=intent,
            case_id=case_id,
            analysis=analysis_res,
            provenance=provenance_res,
            validation=validation_res,
            legal=legal_res,
            similar=similar_res,
            report=report_res,
        )

        follow_up_qs = self._generate_follow_up_questions(
            intent=intent,
            analysis=analysis_res,
            validation=validation_res,
            legal=legal_res,
        )

        return AgentRunResponse(
            conversation_id=conv_id,
            answer=answer,
            execution_status=execution_status,
            intent=intent,
            selected_tools=planned_tools,
            tool_executions=tool_records,
            complaint_analysis=analysis_res,
            evidence_provenance=provenance_res,
            factual_validation=validation_res,
            legal_research=legal_res,
            similar_cases=similar_res,
            investigation_report=report_res,
            follow_up_questions=follow_up_qs,
            requires_human_approval=False,
        )

    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------
    def _check_consequential_action(self, text: str) -> Tuple[bool, Optional[str]]:
        t_low = text.lower()
        for pat in CONSEQUENTIAL_PATTERNS:
            if re.search(pat, t_low):
                return True, (
                    "The requested operation constitutes a consequential statutory action "
                    "(e.g., formal FIR registration, judicial determination, or arrest instruction). "
                    "In compliance with judicial guidelines and police protocol, AI agents are restricted "
                    "to investigative decision support."
                )
        return False, None

    def _extract_case_identifier(self, text: str, fallback_id: Optional[str]) -> Optional[str]:
        if fallback_id and fallback_id.strip():
            return fallback_id.strip()

        # Look for CMP-XXX pattern
        m_cmp = re.search(r"\b(CMP-[A-Za-z0-9_-]+)\b", text, re.IGNORECASE)
        if m_cmp:
            return m_cmp.group(1).upper()

        # Look for UUID pattern
        m_uuid = re.search(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", text, re.IGNORECASE)
        if m_uuid:
            return m_uuid.group(1)

        # Look for "case <id>" pattern
        m_case = re.search(r"\bcase\s+([A-Za-z0-9_-]+)\b", text, re.IGNORECASE)
        if m_case:
            return m_case.group(1)

        return None

    def _plan_workflow(
        self,
        message: str,
        case_id: Optional[str],
        tools_allowed: Optional[List[str]] = None,
    ) -> Tuple[str, List[str]]:
        """
        Dynamically plan which tools to execute based on investigator intent.
        Does not execute unnecessary tools.
        """
        msg_low = message.lower()
        tools: List[str] = []

        is_full_workflow = (
            ("analyse" in msg_low or "analyze" in msg_low or "investigate" in msg_low or "summary" in msg_low or "report" in msg_low)
            and ("contradiction" in msg_low or "legal" in msg_low or "provision" in msg_low or "section" in msg_low or "evidence" in msg_low)
        )

        has_legal_intent = any(k in msg_low for k in ["legal", "provision", "section", "bns", "bnss", "bsa", "ipc", "punishment", "offence", "offense"])
        has_validation_intent = any(k in msg_low for k in ["contradiction", "inconsisten", "unsupported", "missing", "validate", "validation", "gap"])
        has_similar_intent = any(k in msg_low for k in ["similar", "precedent", "precedents", "modus operandi", "past case", "earlier case"])
        has_provenance_intent = any(k in msg_low for k in ["provenance", "evidence span", "offset", "character offset", "verify text", "source span"])
        has_analysis_intent = any(k in msg_low for k in ["analyse", "analyze", "extract", "parties", "facts", "allegation", "complainant", "accused", "victim"])

        if is_full_workflow and case_id:
            intent = "comprehensive_investigation_workflow"
            tools = [
                "analyze_complaint",
                "verify_evidence_provenance",
                "validate_complaint_facts",
                "research_legal_provisions",
                "retrieve_similar_cases",
                "generate_investigation_report",
            ]
        elif has_validation_intent:
            intent = "factual_validation_and_contradictions"
            if case_id:
                tools.append("analyze_complaint")
            tools.append("validate_complaint_facts")
            if "report" in msg_low or "summary" in msg_low:
                tools.append("generate_investigation_report")
        elif has_provenance_intent and case_id:
            intent = "evidence_provenance_verification"
            tools = ["analyze_complaint", "verify_evidence_provenance"]
        elif has_similar_intent:
            intent = "similar_case_retrieval"
            if case_id:
                tools.append("analyze_complaint")
            tools.append("retrieve_similar_cases")
        elif has_legal_intent and not case_id:
            intent = "statutory_legal_research"
            tools = ["research_legal_provisions"]
        elif has_analysis_intent and case_id:
            intent = "complaint_fact_extraction"
            tools = ["analyze_complaint", "verify_evidence_provenance"]
            if has_legal_intent:
                tools.append("research_legal_provisions")
            if "report" in msg_low or "summary" in msg_low:
                tools.append("generate_investigation_report")
        elif case_id:
            # Default for case mention without specific keyword
            intent = "case_investigation_overview"
            tools = ["analyze_complaint", "verify_evidence_provenance", "validate_complaint_facts", "research_legal_provisions"]
        else:
            intent = "general_investigation_qa"
            if has_legal_intent:
                tools.append("research_legal_provisions")
            else:
                tools.append("research_legal_provisions")

        # Apply tools_allowed filter if user explicitly restricted them
        if tools_allowed:
            allowed_set = set(tools_allowed)
            tools = [t for t in tools if t in allowed_set]

        return intent, tools

    def _build_legal_query(self, message: str, analysis: Optional[ComplaintAnalysisOutput]) -> str:
        parts: List[str] = [message]
        if analysis:
            if analysis.property_involved:
                parts.append(" ".join(analysis.property_involved))
            if analysis.weapons_used:
                parts.append(" ".join(analysis.weapons_used))
            if analysis.allegations:
                parts.append(" ".join(analysis.allegations[:2]))
        return " ".join(parts)[:300]

    def _build_similar_case_query(self, message: str, analysis: Optional[ComplaintAnalysisOutput]) -> str:
        if analysis and analysis.raw_text:
            return analysis.raw_text[:400]
        return message[:400]

    def _synthesize_answer(
        self,
        user_message: str,
        intent: str,
        case_id: Optional[str],
        analysis: Optional[ComplaintAnalysisOutput],
        provenance: Optional[EvidenceProvenanceOutput],
        validation: Optional[FactualValidationOutput],
        legal: Optional[LegalResearchOutput],
        similar: Optional[SimilarCaseOutput],
        report: Optional[InvestigationReportOutput],
    ) -> str:
        """
        Synthesize a structured, evidence-grounded response for the investigator.
        """
        # If report tool generated full markdown report, present concise synthesis + report
        sections: List[str] = []

        if report:
            header = f"### 📋 Investigation Support Analysis — Docket {case_id or 'General'}\n"
            summary_box = f"**Executive Summary:** {report.executive_summary}\n"
            sections.append(header)
            sections.append(summary_box)

            # Facts & Allegations
            facts_md = ["**Established Facts:**"]
            for f in report.established_facts[:4]:
                facts_md.append(f"- {f}")
            if report.allegations_and_uncertainties:
                facts_md.append("\n**Reported Allegations & Uncertainties:**")
                for a in report.allegations_and_uncertainties[:3]:
                    facts_md.append(f"- {a}")
            sections.append("\n".join(facts_md))

            # Contradictions & Gaps
            if report.contradictions_and_gaps:
                gaps_md = ["\n**⚠️ Identified Inconsistencies & Information Gaps:**"]
                for g in report.contradictions_and_gaps:
                    gaps_md.append(f"- {g}")
                sections.append("\n".join(gaps_md))

            # Applicable Law
            if report.applicable_legal_framework:
                legal_md = ["\n**⚖️ Verified Applicable Statutory Sections (BNS 2023):**"]
                for l in report.applicable_legal_framework[:3]:
                    legal_md.append(f"{l}")
                sections.append("\n".join(legal_md))

            # Provenance
            if provenance:
                prov_md = (
                    f"\n**🔍 Evidence Provenance:** {provenance.verified_count} facts verified at exact "
                    f"character offsets against raw complaint. Invariant preserved: "
                    f"{'✅ True' if provenance.provenance_invariant_preserved else '❌ Mismatches found'}."
                )
                sections.append(prov_md)

            # Precedent Cases
            if similar and similar.cases:
                sim_md = ["\n**📁 Precedent Modus Operandi & Similar Cases:**"]
                for sc in similar.cases[:2]:
                    sim_md.append(f"- Case `{sc.reference_id}` (Similarity {sc.score}): {sc.summary}")
                sections.append("\n".join(sim_md))

            # Notice
            notice = (
                f"\n---\n> **Human-in-the-Loop Advisory:** {report.human_review_notice}"
            )
            sections.append(notice)
            return "\n\n".join(sections)

        # Single or partial tool synthesis
        if analysis and not validation and not legal:
            comp_name = analysis.complainant or "Not identified"
            accused = ", ".join(analysis.accused_parties) if analysis.accused_parties else "Unknown/None"
            ans_lines = [
                f"### Analysis of Complaint {analysis.reference_id}",
                f"- **Title:** {analysis.title}",
                f"- **Complainant:** {comp_name}",
                f"- **Reported Accused:** {accused}",
                f"- **Incident Date/Time:** {analysis.incident_date or 'Unspecified'} | {analysis.incident_time or 'Unspecified'}",
                f"- **Location:** {analysis.incident_location or 'Unspecified'}",
                f"- **Property/Weapons:** {', '.join(analysis.property_involved) or 'None'} | {', '.join(analysis.weapons_used) or 'None'}",
                f"- **Extracted Facts:** {len(analysis.established_facts)} established, {len(analysis.allegations)} allegations.",
            ]
            if analysis.missing_details:
                ans_lines.append(f"- **Missing Information:** {', '.join(analysis.missing_details)}")
            return "\n".join(ans_lines)

        if validation and not report:
            val_lines = [
                f"### Factual Validation & Contradiction Report {f'for {case_id}' if case_id else ''}",
                f"Total findings identified: **{validation.total_findings}**\n",
            ]
            if validation.contradictions:
                val_lines.append("**Contradictions Detected:**")
                for c in validation.contradictions:
                    val_lines.append(f"- 🔴 **{c.claim_or_statement}**: {c.explanation} *(Severity: {c.severity})*")
            if validation.timeline_inconsistencies:
                val_lines.append("\n**Timeline Inconsistencies:**")
                for t in validation.timeline_inconsistencies:
                    val_lines.append(f"- ⏱️ **{t.claim_or_statement}**: {t.explanation}")
            if validation.missing_statutory_elements:
                val_lines.append("\n**Missing Statutory Elements:**")
                for m in validation.missing_statutory_elements:
                    val_lines.append(f"- ⚠️ **{m.claim_or_statement}**: {m.explanation} — *Action: {m.suggested_action}*")
            if validation.unsupported_claims:
                val_lines.append("\n**Unsupported Claims:**")
                for u in validation.unsupported_claims:
                    val_lines.append(f"- ❓ **{u.claim_or_statement}**: {u.explanation}")
            return "\n".join(val_lines)

        if legal and not analysis:
            leg_lines = [
                f"### Verified Statutory Provisions for: '{legal.query}'",
                f"*{legal.statutory_notes}*\n",
            ]
            for p in legal.provisions:
                ipc_part = f" (IPC Counterpart: {p.ipc_counterpart})" if p.ipc_counterpart else ""
                class_part = ""
                if p.cognizable is not None:
                    class_part = f" — *{'Cognizable' if p.cognizable else 'Non-Cognizable'}, {'Bailable' if p.bailable else 'Non-Bailable'}*"
                leg_lines.append(f"#### {p.title}{ipc_part}{class_part}")
                leg_lines.append(f"> {p.content}\n")
            return "\n".join(leg_lines)

        if similar and not report:
            sim_lines = [
                f"### Similar Historical Cases ({len(similar.cases)} matches)",
                f"> *{similar.disclaimer}*\n",
            ]
            for c in similar.cases:
                sim_lines.append(f"- **Docket {c.reference_id}** (Similarity: {c.score}): {c.summary}")
            return "\n".join(sim_lines)

        # Fallback summary
        return (
            f"Investigation Agent has completed task execution for '{user_message}'. "
            f"Reviewed available tools, verified data provenance, and grounded findings in statutory corpus."
        )

    def _generate_follow_up_questions(
        self,
        intent: str,
        analysis: Optional[ComplaintAnalysisOutput],
        validation: Optional[FactualValidationOutput],
        legal: Optional[LegalResearchOutput],
    ) -> List[str]:
        questions: List[str] = []

        if validation and validation.missing_statutory_elements:
            questions.append("Would you like to generate a formal clarification questionnaire for the complainant regarding missing details?")
        if validation and validation.contradictions:
            questions.append("Should I draft specific interrogation questions to cross-examine the contradictory statements?")
        if legal and legal.provisions:
            top_prov = legal.provisions[0].title
            questions.append(f"Do you want me to analyze whether all essential ingredients of {top_prov} are fulfilled?")
        if analysis and analysis.property_involved:
            questions.append("Should we log evidence preservation notices (Sec 91 BNSS) for the reported property/CCTV footage?")

        if not questions:
            questions = [
                "Would you like to compare this case against similar historical investigation records?",
                "Should I formulate an FIR draft based on the validated facts for your review?",
            ]

        return questions[:3]


# Singleton Orchestrator instance
investigation_agent_orchestrator = InvestigationAgentOrchestrator()
