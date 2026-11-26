"""
tests/test_investigation_agent_api.py — Integration tests for Investigation Agent API endpoints.
Validates authentication, authorization, schema validation, and tool execution over HTTP.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def api_client():
    client = TestClient(app)
    return client


@pytest.fixture(scope="module")
def test_officer_token():
    db = SessionLocal()
    # Check if officer exists or create
    officer = db.query(User).filter(User.email == "test_officer@police.gov.in").first()
    if not officer:
        officer = User(
            id=uuid.uuid4(),
            email="test_officer@police.gov.in",
            full_name="Sub-Inspector Anitha Raman",
            role=UserRole.investigator,
            hashed_password="hashed_pw_test",
            is_active=True,
        )
        db.add(officer)
        db.commit()
        db.refresh(officer)
    db.close()

    token = create_access_token(subject=str(officer.id))
    return token


def test_agent_endpoint_requires_auth(api_client):
    """Verify endpoint rejects unauthenticated requests with 401."""
    res = api_client.post("/api/v1/assistant/agent/run", json={"message": "Analyze theft case"})
    assert res.status_code == 401


def test_tools_endpoint_lists_all_six_tools(api_client, test_officer_token):
    """Verify /assistant/tools returns the 6 core tools with descriptions."""
    headers = {"Authorization": f"Bearer {test_officer_token}"}
    res = api_client.get("/api/v1/assistant/tools", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "analyze_complaint" in tool_names
    assert "verify_evidence_provenance" in tool_names
    assert "validate_complaint_facts" in tool_names
    assert "research_legal_provisions" in tool_names
    assert "retrieve_similar_cases" in tool_names
    assert "generate_investigation_report" in tool_names


def test_cases_endpoint_returns_list(api_client, test_officer_token):
    """Verify /assistant/cases returns list of cases."""
    headers = {"Authorization": f"Bearer {test_officer_token}"}
    res = api_client.get("/api/v1/assistant/cases", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_agent_run_endpoint_legal_research(api_client, test_officer_token):
    """Verify executing legal research through API."""
    headers = {"Authorization": f"Bearer {test_officer_token}"}
    payload = {
        "message": "Which section of Bharatiya Nyaya Sanhita applies to theft of property?",
    }
    res = api_client.post("/api/v1/assistant/agent/run", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] in ["completed", "partial"]
    assert "answer" in data
    assert len(data["selected_tools"]) > 0
    assert "research_legal_provisions" in data["selected_tools"]


def test_legacy_query_endpoint_backward_compatibility(api_client, test_officer_token):
    """Verify legacy /assistant/query continues to function."""
    headers = {"Authorization": f"Bearer {test_officer_token}"}
    payload = {
        "question": "What is Section 303 BNS?",
    }
    res = api_client.post("/api/v1/assistant/query", headers=headers, json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "sources" in data
    assert "citations" in data
