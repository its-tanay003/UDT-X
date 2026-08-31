"""UDT-X Risk Engine & Alert Manager — Integration Tests (Phase 10).

Tests:
1. Risk Engine composite score calculation combining confidence, deviation,
   evidence, correlation, and asset criticality.
2. Alert Manager REST endpoints: GET/POST /alerts, GET /incidents, GET /performance.
3. Alert Exporter: CEF & Syslog RFC 5424 export formats on /alerts/export.
4. WebSocket live stream: Connects to /ws/live and receives real-time broadcast.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from correlation.models import AttackChainProgression, Incident, IncidentStatus
from risk_engine.calculator import AssetCriticalityRegistry, RiskEngineCalculator
from schema.models import Alert, EvidenceItem, MitreAttack, SeverityLevel
from services.api.app.main import app


def _make_test_alert(
    alert_id: str = "alt-phase10-01",
    src_ip: str = "10.0.0.1",  # Tier 1 Critical Asset (2.5 multiplier)
    dst_ip: str = "198.51.100.77",
    threat_class: str = "C2_BEACONING",
    confidence: float = 0.90,
) -> Alert:
    return Alert(
        alert_id=alert_id,
        timestamp=datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="TCP",
        threat_class=threat_class,
        severity=SeverityLevel.HIGH,
        confidence=confidence,
        risk_score=75.0,
        evidence=[
            EvidenceItem(key="PERIODICITY_SCORE", value="0.98"),
            EvidenceItem(key="IOC_MATCH", value="198.51.100.77"),
        ],
        mitre=[
            MitreAttack(
                technique_id="T1071",
                technique_name="Application Layer Protocol",
            )
        ],
        title="Command & Control Beaconing to APT29 Team Server",
    )


def test_risk_calculator_composite_scoring() -> None:
    calc = RiskEngineCalculator(AssetCriticalityRegistry())
    alert = _make_test_alert()

    # Normal isolated alert on critical asset
    risk_isolated = calc.calculate_alert_risk(alert)
    assert 50.0 <= risk_isolated <= 100.0

    # Incident with full kill chain escalates score
    incident = Incident(
        incident_id="inc-test-01",
        title="Full Kill Chain Attack",
        created_at=datetime.now(UTC),
        last_updated=datetime.now(UTC),
        primary_host_ip=alert.src_ip,
        target_destination_ips=[alert.dst_ip],
        alert_ids=[alert.alert_id],
        threat_classes=["RECONNAISSANCE", "C2_BEACONING", "EXFILTRATION"],
        attack_chain=AttackChainProgression.FULL_KILL_CHAIN,
        severity=SeverityLevel.CRITICAL,
        risk_score=95.0,
    )
    risk_correlated = calc.calculate_alert_risk(alert, incident=incident)
    assert risk_correlated >= risk_isolated


def test_alert_and_incident_api_endpoints() -> None:
    client = TestClient(app)

    # 1. Post synthetic alert
    alert = _make_test_alert(alert_id="alt-api-test-99")
    post_resp = client.post("/alerts", json=alert.model_dump(mode="json"))
    assert post_resp.status_code == 201

    # 2. Retrieve alert by ID
    get_resp = client.get("/alerts/alt-api-test-99")
    assert get_resp.status_code == 200
    assert get_resp.json()["alert_id"] == "alt-api-test-99"

    # 3. Filter alerts
    list_resp = client.get("/alerts?threat_class=C2_BEACONING")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # 4. Post synthetic incident
    incident = Incident(
        incident_id="inc-api-test-88",
        title="Active Attack Campaign",
        created_at=datetime.now(UTC),
        last_updated=datetime.now(UTC),
        primary_host_ip="192.168.1.50",
        target_destination_ips=["198.51.100.77"],
        alert_ids=["alt-api-test-99"],
        threat_classes=["C2_BEACONING"],
        attack_chain=AttackChainProgression.GENERIC_MULTI_ALERT,
        status=IncidentStatus.ACTIVE,
        severity=SeverityLevel.HIGH,
        risk_score=85.0,
    )
    inc_post = client.post("/incidents", json=incident.model_dump(mode="json"))
    assert inc_post.status_code == 201

    # 5. Retrieve incident
    inc_get = client.get("/incidents/inc-api-test-88")
    assert inc_get.status_code == 200
    assert inc_get.json()["incident_id"] == "inc-api-test-88"

    # 6. Performance metrics
    perf_resp = client.get("/performance")
    assert perf_resp.status_code == 200
    perf_data = perf_resp.json()
    assert "total_alerts" in perf_data
    assert perf_data["total_alerts"] >= 1


def test_cef_and_syslog_export_endpoint() -> None:
    client = TestClient(app)
    alert = _make_test_alert(alert_id="alt-export-01")
    client.post("/alerts", json=alert.model_dump(mode="json"))

    # Test CEF Export
    cef_resp = client.get("/alerts/export?format=cef")
    assert cef_resp.status_code == 200
    assert "CEF:0|UDTX|UDT-X Telemetry Platform" in cef_resp.text
    assert "src=10.0.0.1" in cef_resp.text

    # Test Syslog RFC 5424 Export
    syslog_resp = client.get("/alerts/export?format=syslog")
    assert syslog_resp.status_code == 200
    assert "udtx-sensor udtx-risk-engine" in syslog_resp.text


def test_websocket_realtime_stream() -> None:
    client = TestClient(app)

    with client.websocket_connect("/ws/live") as ws:
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "CONNECTED"

        # Ping-Pong test
        ws.send_text("ping")
        pong_msg = json.loads(ws.receive_text())
        assert pong_msg["type"] == "PONG"
