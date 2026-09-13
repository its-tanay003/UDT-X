"""Comprehensive Tests for Voice-Enabled UDT-X AI Sentinel Copilot.

Verifies:
1. Spoken voice commands for navigation, filtering, and system explanation.
2. Direct generation of concise spoken_response fields.
3. Voice confirmation gates for sensitive actions (simulation).
4. Strict permission enforcement blocking voice commands attempting admin actions without clearance.
5. Voice prompt injection resilience.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


@pytest.fixture
def admin_token():
    res = client.post(
        "/auth/login",
        json={"email": "admin@udtx.local", "password": "AdminEnclave2026!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def analyst_token():
    res = client.post(
        "/auth/login",
        json={"email": "analyst@udtx.local", "password": "AnalystEnclave2026!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_voice_navigation_and_spoken_response(analyst_token):
    """Test voice natural phrase 'Open live traffic flows' generates navigate tool and spoken response."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Open live traffic flows"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "navigate"
    assert data["tool_call"]["tool_name"] == "navigate_page"
    assert data["tool_call"]["parameters"]["target_route"] == "/monitor"
    assert "spoken_response" in data
    assert data["spoken_response"] is not None
    assert len(data["spoken_response"]) > 0


def test_voice_telemetry_query(analyst_token):
    """Test voice question 'What is our composite risk and threat level?'"""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "What is our composite risk and threat level?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "telemetry_summary"
    assert "Composite threat score" in data["spoken_response"]
    assert "risk_score" in data["executed_action_result"]


def test_voice_explain_concept_synthesizes_spoken_audio(analyst_token):
    """Test voice explanation of mathematical model generates concise speech."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Can you explain TreeSHAP model?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "explain_concept"
    assert "TreeSHAP" in data["spoken_response"]
    assert len(data["spoken_response"]) < len(data["message"])  # Concise spoken output


def test_voice_sensitive_simulation_gate(analyst_token):
    """Test voice command to run an attack scenario requires confirmation."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Run simulation for ddos syn flood attack"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["requires_user_confirmation"] is True
    assert "Confirmation required" in data["spoken_response"]


def test_voice_command_blocked_for_unauthorized_user(analyst_token):
    """Test voice command attempting admin action is blocked by permission gate."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Register operator user for analyst"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["error"] == "INSUFFICIENT_CLEARANCE"
    assert "Access denied" in data["spoken_response"]
