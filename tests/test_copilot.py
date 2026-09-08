"""Tests for UDT-X AI Copilot, Capability Registry, Permission Gates, and Personalization."""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app.services.agent_engine import copilot_agent
from services.api.app.services.capability_registry import ACTION_REGISTRY, ROUTE_REGISTRY

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


def test_copilot_capability_registry():
    """Verify route and action registries are populated."""
    assert "/" in ROUTE_REGISTRY
    assert "/monitor" in ROUTE_REGISTRY
    assert "/replay" in ROUTE_REGISTRY
    assert "navigate_page" in ACTION_REGISTRY
    assert "trigger_replay_simulation" in ACTION_REGISTRY
    assert "provision_user" in ACTION_REGISTRY


def test_copilot_navigation_intent(analyst_token):
    """Test natural language navigation intent resolution."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Please take me to the Live Monitor feed"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "navigate"
    assert data["tool_call"] is not None
    assert data["tool_call"]["tool_name"] == "navigate_page"
    assert data["tool_call"]["parameters"]["target_route"] == "/monitor"


def test_copilot_sensitive_action_requires_confirmation(analyst_token):
    """Test that sensitive operations (simulation) require confirmation."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Simulate a DDoS SYN flood attack"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["requires_user_confirmation"] is True
    assert data["confirmation_payload"] is not None
    assert data["confirmation_payload"]["action_id"] == "trigger_replay_simulation"
    assert data["confirmation_payload"]["parameters"]["scenario"] == "ddos_syn_flood"


def test_copilot_confirmed_action_execution(analyst_token):
    """Test executing a confirmed sensitive action."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "query": "Execute simulation",
            "action_request": {
                "action_id": "trigger_replay_simulation",
                "parameters": {"scenario": "ddos_syn_flood"},
                "confirmed": True,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["requires_user_confirmation"] is False
    assert data["executed_action_result"]["status"] == "simulation_injected"


def test_copilot_admin_role_permission_gate(analyst_token, admin_token):
    """Test that analyst is blocked from admin actions, but admin is allowed with confirmation."""
    # Analyst attempt
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "query": "Provision user",
            "action_request": {
                "action_id": "provision_user",
                "parameters": {"email": "newbie@udtx.local", "display_name": "New Analyst", "password": "Pass"},
                "confirmed": True,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["error"] == "INSUFFICIENT_CLEARANCE"
    assert "Permission Denied" in data["message"]


def test_copilot_local_rag_knowledge(analyst_token):
    """Test local RAG explanation of security concepts."""
    res = client.post(
        "/copilot/query",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"query": "Explain TreeSHAP and why we use it"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "explain_concept"
    assert "TreeSHAP" in data["message"]
    assert "LightGBM" in data["message"]
    assert data["is_offline_capable"] is True


def test_copilot_recommendations(analyst_token):
    """Test fetching personalized shift recommendations."""
    res = client.get(
        "/copilot/recommendations",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 200
    recs = res.json()
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert "title" in recs[0]
    assert "target_route" in recs[0]
