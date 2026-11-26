"""
api/v1/assistant.py — AI Investigation Agent and Grounded Legal Assistant endpoints.
Integrates autonomous multi-step tool-calling agent with existing RAG capabilities.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.agent.orchestrator import investigation_agent_orchestrator
from app.agent.schemas import AgentRunRequest, AgentRunResponse
from app.agent.tools import (
    complaint_analysis_tool,
    evidence_provenance_tool,
    factual_validation_tool,
    legal_research_tool,
    similar_case_tool,
    investigation_report_tool,
)
from app.core.dependencies import get_current_user, get_db
from app.models.complaint import Complaint
from app.models.user import User
from app.services.assistant_service import query_investigation_assistant
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["Investigation Assistant"])


# ------------------------------------------------------------------------------
# Legacy / Backward-Compatible Schemas
# ------------------------------------------------------------------------------
class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    complaint_id: Optional[uuid.UUID] = None


class CitationItem(BaseModel):
    index: int
    title: str
    source: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None


class AssistantQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    citations: List[str] = []
    is_retrieval_only: bool = False


# ------------------------------------------------------------------------------
# Tool Metadata Schema
# ------------------------------------------------------------------------------
class ToolInfo(BaseModel):
    name: str
    display_name: str
    description: str


class ToolListResponse(BaseModel):
    tools: List[ToolInfo]


class CaseSummaryItem(BaseModel):
    id: str
    reference_id: str
    title: str
    incident_date: Optional[str] = None
    incident_location: Optional[str] = None
    status: str


# ------------------------------------------------------------------------------
# 1. Autonomous AI Investigation Agent Endpoint
# ------------------------------------------------------------------------------
@router.post("/agent/run", response_model=AgentRunResponse)
def run_investigation_agent(
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Execute the autonomous AI Investigation Agent.
    Dynamically plans tasks, invokes tools (Complaint Analysis, Evidence Provenance,
    Factual Validation, Legal Research, Similar Case Retrieval, Report Generation),
    maintains conversation state, and returns evidence-grounded findings.
    """
    result = investigation_agent_orchestrator.execute(db=db, request=payload)

    create_audit_log(
        db=db,
        action="agent_investigation_executed",
        resource_type="investigation_agent",
        resource_id=payload.complaint_id,
        user_id=current_user.id,
        details={
            "intent": result.intent,
            "status": result.execution_status,
            "tools_called": [t.tool_name for t in result.tool_executions],
            "total_tools": len(result.tool_executions),
        },
    )

    return result


# ------------------------------------------------------------------------------
# 2. Available Agent Tools Metadata Endpoint
# ------------------------------------------------------------------------------
@router.get("/tools", response_model=ToolListResponse)
def list_agent_tools(
    current_user: User = Depends(get_current_user),
) -> Any:
    """List available tools in the AI Investigation Agent suite."""
    all_tools = [
        ToolInfo(
            name=complaint_analysis_tool.name,
            display_name=complaint_analysis_tool.display_name,
            description=complaint_analysis_tool.description,
        ),
        ToolInfo(
            name=evidence_provenance_tool.name,
            display_name=evidence_provenance_tool.display_name,
            description=evidence_provenance_tool.description,
        ),
        ToolInfo(
            name=factual_validation_tool.name,
            display_name=factual_validation_tool.display_name,
            description=factual_validation_tool.description,
        ),
        ToolInfo(
            name=legal_research_tool.name,
            display_name=legal_research_tool.display_name,
            description=legal_research_tool.description,
        ),
        ToolInfo(
            name=similar_case_tool.name,
            display_name=similar_case_tool.display_name,
            description=similar_case_tool.description,
        ),
        ToolInfo(
            name=investigation_report_tool.name,
            display_name=investigation_report_tool.display_name,
            description=investigation_report_tool.description,
        ),
    ]
    return ToolListResponse(tools=all_tools)


# ------------------------------------------------------------------------------
# 3. Helper: List/Search Cases for Agent Selector
# ------------------------------------------------------------------------------
@router.get("/cases", response_model=List[CaseSummaryItem])
def list_cases_for_agent(
    search: Optional[str] = Query(None),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve indexed complaint dockets for selection in the Investigation Agent."""
    query = db.query(Complaint)
    if search:
        s_term = f"%{search}%"
        query = query.filter(
            or_(
                Complaint.reference_id.ilike(s_term),
                Complaint.title.ilike(s_term),
                Complaint.incident_location.ilike(s_term),
            )
        )
    complaints = query.order_by(Complaint.created_at.desc()).limit(limit).all()

    return [
        CaseSummaryItem(
            id=str(c.id),
            reference_id=c.reference_id,
            title=c.title,
            incident_date=c.incident_date.isoformat() if c.incident_date else None,
            incident_location=c.incident_location,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
        )
        for c in complaints
    ]


# ------------------------------------------------------------------------------
# 4. Legacy Grounded Assistant Query Endpoint
# ------------------------------------------------------------------------------
@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Ask an investigation-support question. Answers are grounded in retrieved case documents and legal provisions."""
    complaint_context = None
    if payload.complaint_id:
        complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
        if complaint:
            complaint_context = complaint.raw_text or complaint.extracted_text

    result = query_investigation_assistant(
        question=payload.question,
        complaint_context=complaint_context,
    )

    create_audit_log(
        db=db,
        action="assistant_queried",
        resource_type="rag_assistant",
        user_id=current_user.id,
        details={"question_length": len(payload.question)},
    )

    return AssistantQueryResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        citations=result.get("citations", []),
        is_retrieval_only=result.get("is_retrieval_only", False),
    )
