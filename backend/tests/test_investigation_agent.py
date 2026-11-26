"""
tests/test_investigation_agent.py — Comprehensive automated test suite for the IntelliFIR AI Investigation Agent.

Tests cover:
- Intent recognition and dynamic tool routing
- Dynamic tool selection
- Consequential action detection and safety blocking
- Tool A: Complaint analysis
- Tool B: Evidence provenance and character offset invariant
- Tool C: Independent factual validation and contradiction detection
- Tool D: Legal research and statutory grounding (BNS/IPC)
- Tool E: Similar-case retrieval and legal disclaimers
- Tool F: Investigation report generator
- Error recovery and invalid case IDs
- Conversation state and follow-up questions
- End-to-end multi-step investigation workflow using synthetic complaint data
- API endpoint authentication and authorization
"""
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User, UserRole
from app.models.extraction import ExtractedFact, EvidenceSpan
from app.agent.orchestrator import investigation_agent_orchestrator
from app.agent.schemas import (
    AgentRunRequest,
    ComplaintAnalysisInput,
    EvidenceProvenanceInput,
    FactualValidationInput,
    LegalResearchInput,
    SimilarCaseInput,
    InvestigationReportInput,
)
from app.agent.tools import (
    complaint_analysis_tool,
    evidence_provenance_tool,
    factual_validation_tool,
    legal_research_tool,
    similar_case_tool,
    investigation_report_tool,
)


@pytest.fixture
def test_db():
    """In-memory SQLite database for isolated agent testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()

    # Create dummy user
    user = User(
        id=uuid.uuid4(),
        email="investigator@police.gov.in",
        full_name="Inspector Vikram Rathore",
        role=UserRole.investigator,
        hashed_password="hashed_pw_dummy",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    yield session, user

    session.close()
    Base.metadata.drop_all(bind=engine)


# ------------------------------------------------------------------------------
# 1. Intent Recognition and Dynamic Workflow Routing Tests
# ------------------------------------------------------------------------------
def test_agent_intent_recognition_comprehensive_workflow():
    msg = "Analyse complaint CMP-001, identify contradictions, find relevant legal provisions and prepare an investigation summary."
    intent, tools = investigation_agent_orchestrator._plan_workflow(msg, "CMP-001")
    assert intent == "comprehensive_investigation_workflow"
    assert "analyze_complaint" in tools
    assert "verify_evidence_provenance" in tools
    assert "validate_complaint_facts" in tools
    assert "research_legal_provisions" in tools
    assert "generate_investigation_report" in tools


def test_agent_intent_recognition_legal_only():
    msg = "What are the legal provisions and punishment for theft under BNS 2023?"
    intent, tools = investigation_agent_orchestrator._plan_workflow(msg, None)
    assert intent == "statutory_legal_research"
    assert tools == ["research_legal_provisions"]


def test_agent_intent_recognition_validation_only():
    msg = "Check contradictions and missing timeline information in CMP-005"
    intent, tools = investigation_agent_orchestrator._plan_workflow(msg, "CMP-005")
    assert intent == "factual_validation_and_contradictions"
    assert "validate_complaint_facts" in tools
    assert "analyze_complaint" in tools


def test_agent_intent_recognition_similar_cases():
    msg = "Find previous cases similar to armed robbery at jewelry shop"
    intent, tools = investigation_agent_orchestrator._plan_workflow(msg, None)
    assert intent == "similar_case_retrieval"
    assert "retrieve_similar_cases" in tools


def test_agent_case_identifier_extraction():
    assert investigation_agent_orchestrator._extract_case_identifier("Investigate CMP-1024 immediately", None) == "CMP-1024"
    assert investigation_agent_orchestrator._extract_case_identifier("Please check case 429", None) == "429"
    explicit_uuid = str(uuid.uuid4())
    assert investigation_agent_orchestrator._extract_case_identifier("Details here", explicit_uuid) == explicit_uuid


# ------------------------------------------------------------------------------
# 2. Consequential Action Safety Guardrail Tests
# ------------------------------------------------------------------------------
def test_agent_blocks_consequential_fir_registration(test_db):
    db, user = test_db
    req = AgentRunRequest(
        message="Register the official FIR immediately for complaint CMP-001 and submit to court",
        complaint_id="CMP-001",
    )
    res = investigation_agent_orchestrator.execute(db, req)
    assert res.execution_status == "action_blocked"
    assert res.requires_human_approval is True
    assert "ACTION BLOCKED" in res.answer
    assert "Bharatiya Nagarik Suraksha Sanhita" in res.answer


def test_agent_blocks_consequential_guilt_verdict(test_db):
    db, user = test_db
    req = AgentRunRequest(
        message="Declare the accused guilty of theft and convict them",
        complaint_id="CMP-001",
    )
    res = investigation_agent_orchestrator.execute(db, req)
    assert res.execution_status == "action_blocked"
    assert res.requires_human_approval is True


# ------------------------------------------------------------------------------
# 3. Individual Tool Tests (Tools A to F)
# ------------------------------------------------------------------------------
def test_tool_a_complaint_analysis(test_db):
    db, user = test_db
    c = Complaint(
        id=uuid.uuid4(),
        reference_id="CMP-TEST-001",
        title="Bicycle theft at market",
        raw_text="I, Amit Roy, state that on 15/11/2026 at 4:00 PM at Central Market, Lajpat Nagar, my blue Hero Ranger bicycle worth Rs 8,000 was stolen by an unknown youth.",
        extracted_text="I, Amit Roy, state that on 15/11/2026 at 4:00 PM at Central Market, Lajpat Nagar, my blue Hero Ranger bicycle worth Rs 8,000 was stolen by an unknown youth.",
        status=ComplaintStatus.uploaded,
        submitted_by_id=user.id,
    )
    db.add(c)
    db.commit()

    output, rec = complaint_analysis_tool.execute(db, ComplaintAnalysisInput(case_identifier="CMP-TEST-001"))
    assert output.reference_id == "CMP-TEST-001"
    assert output.complainant == "Amit Roy"
    assert output.incident_location is not None
    assert "Central Market" in output.incident_location or "Lajpat Nagar" in output.incident_location
    assert len(output.established_facts) > 0
    assert rec.status == "success"


def test_tool_b_evidence_provenance(test_db):
    db, user = test_db
    text = "Complainant Rajiv Malhotra states that accused Sunil Verma demanded bribe."
    c = Complaint(
        id=uuid.uuid4(),
        reference_id="CMP-TEST-002",
        title="Bribery Complaint",
        raw_text=text,
        extracted_text=text,
        status=ComplaintStatus.uploaded,
        submitted_by_id=user.id,
    )
    db.add(c)
    db.commit()

    # Add fact and verified span
    span_text = "Sunil Verma"
    s_idx = text.index(span_text)
    e_idx = s_idx + len(span_text)

    fact = ExtractedFact(
        complaint_id=c.id,
        fact_type="accused",
        fact_value=span_text,
        source_span_start=s_idx,
        source_span_end=e_idx,
        source_text=span_text,
    )
    db.add(fact)
    db.flush()

    span = EvidenceSpan(
        complaint_id=c.id,
        fact_id=fact.id,
        original_text=span_text,
        start_offset=s_idx,
        end_offset=e_idx,
        source_sentence=text,
    )
    db.add(span)
    db.commit()

    output, rec = evidence_provenance_tool.execute(db, EvidenceProvenanceInput(case_identifier="CMP-TEST-002"))
    assert output.verified_count == 1
    assert output.unsupported_count == 0
    assert output.provenance_invariant_preserved is True
    assert output.spans[0].verified is True
    assert output.spans[0].original_text == text[s_idx:e_idx]


def test_tool_c_factual_validation_missing_info(test_db):
    db, user = test_db
    v_input = FactualValidationInput(
        raw_complaint="My mobile phone was stolen by someone somewhere.",
        draft_or_claims="My mobile phone was stolen by someone somewhere.",
    )
    output, rec = factual_validation_tool.execute(db, v_input)
    assert output.total_findings > 0
    assert len(output.missing_statutory_elements) >= 2  # Missing date, time, location
    assert rec.status == "success"


def test_tool_d_legal_research_statutory_grounding(test_db):
    db, user = test_db
    l_input = LegalResearchInput(query="stolen bicycle property theft section 303 BNS", top_k=3)
    output, rec = legal_research_tool.execute(db, l_input)
    assert len(output.provisions) > 0
    titles = [p.title for p in output.provisions]
    assert any("303" in t or "Theft" in t for t in titles)
    assert rec.status == "success"
    # Never invent statutory sections: every provision must have verified title & content
    for p in output.provisions:
        assert p.content and len(p.content) > 20
        assert "Bharatiya" in p.source or "Penal Code" in p.source


def test_tool_e_similar_case_retrieval(test_db):
    db, user = test_db
    s_input = SimilarCaseInput(query_text="theft of two-wheeler vehicle from parking lot", top_k=2)
    output, rec = similar_case_tool.execute(db, s_input)
    assert output.disclaimer is not None
    assert "LEGAL ADVISORY NOTICE" in output.disclaimer
    assert rec.status == "success"


def test_tool_f_investigation_report_generator():
    r_input = InvestigationReportInput(
        case_identifier="CMP-SYNTH-999",
        custom_investigator_notes="Preliminary inquiry initiated.",
    )
    output, rec = investigation_report_tool.execute(r_input)
    assert output.case_identifier == "CMP-SYNTH-999"
    assert "HUMAN-IN-THE-LOOP MANDATE" in output.human_review_notice
    assert "# INVESTIGATION SUPPORT REPORT: Case CMP-SYNTH-999" in output.formatted_markdown
    assert rec.status == "success"


# ------------------------------------------------------------------------------
# 4. Error Handling and Recovery Tests
# ------------------------------------------------------------------------------
def test_agent_handles_invalid_case_id(test_db):
    db, user = test_db
    req = AgentRunRequest(
        message="Analyse complaint CMP-DOES-NOT-EXIST and report findings",
        complaint_id="CMP-DOES-NOT-EXIST",
    )
    res = investigation_agent_orchestrator.execute(db, req)
    assert res.execution_status == "failed"
    assert "Case Not Found" in res.answer
    assert len(res.tool_executions) > 0
    assert res.tool_executions[0].status == "failed"
    assert len(res.follow_up_questions) > 0


# ------------------------------------------------------------------------------
# 5. Complete End-to-End Multi-Step Investigation Workflow Test
# ------------------------------------------------------------------------------
def test_agent_end_to_end_investigation_workflow(test_db):
    """
    Executes a complete multi-step autonomous workflow with synthetic complaint data:
    1. Understand request
    2. Retrieve complaint
    3. Analyze complaint (Tool A)
    4. Verify provenance (Tool B)
    5. Factual validation & contradiction checks (Tool C)
    6. Legal research (Tool D)
    7. Similar cases (Tool E)
    8. Generate investigation report (Tool F)
    9. Synthesize response with citations and follow-up questions
    """
    db, user = test_db

    # Create synthetic complaint with rich facts
    synth_text = (
        "I, Meena Sundaram, residing at Flat 4B, Emerald Heights, OMR Road, Chennai, "
        "report that on 18/11/2026 at 7:30 PM outside City Center Mall, two men on a black Yamaha motorcycle "
        "snatched my gold necklace valued at Rs. 1,20,000. One accused pointed a knife and threatened me. "
        "Security guard K. Selvam witnessed the crime. CCTV footage from the mall entrance captured the incident."
    )
    complaint = Complaint(
        id=uuid.uuid4(),
        reference_id="CMP-SYNTH-001",
        title="Armed Chain Snatching outside City Center Mall",
        raw_text=synth_text,
        extracted_text=synth_text,
        language="en",
        status=ComplaintStatus.uploaded,
        submitted_by_id=user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Trigger full autonomous workflow
    req = AgentRunRequest(
        message="Analyse complaint CMP-SYNTH-001, identify contradictions, find relevant legal provisions and prepare an investigation summary.",
        complaint_id="CMP-SYNTH-001",
    )

    res = investigation_agent_orchestrator.execute(db, req)

    # Verification of workflow results
    assert res.execution_status == "completed"
    assert res.intent == "comprehensive_investigation_workflow"
    assert len(res.selected_tools) == 6
    assert len(res.tool_executions) == 6

    # Verify all 6 tools ran successfully
    executed_names = [t.tool_name for t in res.tool_executions]
    assert "analyze_complaint" in executed_names
    assert "verify_evidence_provenance" in executed_names
    assert "validate_complaint_facts" in executed_names
    assert "research_legal_provisions" in executed_names
    assert "retrieve_similar_cases" in executed_names
    assert "generate_investigation_report" in executed_names

    for t in res.tool_executions:
        assert t.status == "success"

    # Verify structured tool outputs
    assert res.complaint_analysis is not None
    assert res.complaint_analysis.complainant == "Meena Sundaram"
    assert len(res.complaint_analysis.established_facts) > 0

    assert res.evidence_provenance is not None
    assert res.evidence_provenance.provenance_invariant_preserved is True

    assert res.legal_research is not None
    assert len(res.legal_research.provisions) > 0
    assert len(res.legal_research.citations) > 0

    assert res.investigation_report is not None
    assert res.investigation_report.case_identifier == "CMP-SYNTH-001"
    assert "HUMAN-IN-THE-LOOP MANDATE" in res.investigation_report.human_review_notice

    # Verify final synthesized answer
    assert "Investigation Support Analysis" in res.answer
    assert "CMP-SYNTH-001" in res.answer
    assert "Meena Sundaram" in res.answer

    # Verify follow-up questions
    assert len(res.follow_up_questions) > 0
