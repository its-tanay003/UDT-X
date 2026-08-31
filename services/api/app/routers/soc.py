"""UDT-X Alert & Incident REST and WebSocket Endpoints (Phase 10)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from alert_manager.exporter import AlertExporter
from alert_manager.store import global_alert_store
from correlation.models import Incident
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from schema.models import Alert

logger = logging.getLogger("udtx.api.router")

router = APIRouter(tags=["SOC & Alerts"])

# Active WebSocket dashboard clients
connected_websockets: set[WebSocket] = set()


async def broadcast_ws_message(message: dict[str, Any]) -> None:
    """Broadcast alert/incident event to all connected dashboard websockets."""
    disconnected: list[WebSocket] = []
    text_data = json.dumps(message)
    for ws in connected_websockets:
        try:
            await ws.send_text(text_data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected_websockets.discard(ws)


@router.get("/alerts", response_model=list[Alert])
async def get_alerts(
    threat_class: str | None = Query(None, description="Filter by threat class"),
    severity: str | None = Query(None, description="Filter by severity"),
    min_risk: float | None = Query(None, description="Filter by minimum risk"),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Alert]:
    """Retrieve scored alerts from TimescaleDB / Alert Store."""
    return global_alert_store.get_alerts(
        threat_class=threat_class,
        severity=severity,
        min_risk=min_risk,
        limit=limit,
    )


@router.get("/alerts/stats")
async def get_threat_statistics(
    time_range: str = Query(default="24h", pattern="^(1h|24h|7d|30d)$"),
) -> dict[str, Any]:
    """Breakdown of alerts, counts, risk scores, and severities by threat class."""
    return global_alert_store.get_threat_stats(time_range=time_range)


@router.get("/alerts/export")
async def export_alerts(
    format: str = Query("cef", description="Export format: 'cef' or 'syslog'"),
    limit: int = Query(100, ge=1, le=1000),
) -> Response:
    """Export alerts in CEF or Syslog RFC 5424 formats for SIEM ingestion."""
    alerts = global_alert_store.get_alerts(limit=limit)
    content = AlertExporter.export_all(alerts, format_type=format)
    media_type = "text/plain"
    return Response(content=content, media_type=media_type)


@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert_by_id(alert_id: str) -> Alert:
    """Retrieve a single alert by its unique alert_id."""
    alert = global_alert_store.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts", response_model=Alert, status_code=201)
async def ingest_and_broadcast_alert(alert: Alert) -> Alert:
    """Ingest, store, and broadcast an alert in real time."""
    saved = global_alert_store.save_alert(alert)
    asyncio.create_task(
        broadcast_ws_message(
            {"type": "NEW_ALERT", "data": saved.model_dump(mode="json")}
        )
    )
    return saved


@router.get("/incidents", response_model=list[Incident])
async def get_incidents(
    status: str | None = Query(None, description="Filter by incident status"),
    min_risk: float | None = Query(None, description="Filter by minimum risk"),
    limit: int = Query(50, ge=1, le=500),
) -> list[Incident]:
    """Retrieve correlated multi-alert Incidents."""
    return global_alert_store.get_incidents(
        status=status,
        min_risk=min_risk,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident_by_id(incident_id: str) -> Incident:
    """Retrieve a single correlated incident by its incident_id."""
    inc = global_alert_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.post("/incidents", response_model=Incident, status_code=201)
async def ingest_and_broadcast_incident(incident: Incident) -> Incident:
    """Ingest, store, and broadcast an incident in real time."""
    saved = global_alert_store.save_incident(incident)
    asyncio.create_task(
        broadcast_ws_message(
            {"type": "NEW_INCIDENT", "data": saved.model_dump(mode="json")}
        )
    )
    return saved


@router.get("/performance")
async def get_performance_metrics() -> dict[str, Any]:
    """SOC/SIEM real-time engine processing performance metrics."""
    return global_alert_store.get_performance_metrics()


@router.get("/graph")
async def get_evidence_graph_topology(
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    """Fetch nodes & edges from Neo4j evidence graph."""
    from correlation.graph_client import Neo4jEvidenceGraph

    graph_client = Neo4jEvidenceGraph()
    try:
        return graph_client.get_graph_topology(limit=limit)
    finally:
        graph_client.close()


@router.post("/replay/{scenario}")
async def replay_scenario_simulation(
    scenario: str,
    background_tasks: Any = None,
) -> dict[str, Any]:
    """Replay simulation test scenarios generating live alerts and incidents.

    Supported scenarios:
    - kill_chain (Recon -> C2 Beaconing -> Exfiltration)
    - ddos_surge (SYN Flood + UDP Amplification)
    - dga_c2 (DGA Domain Fluxing + C2 Beacon)
    - exfil_spike (Large Volume Asymmetric Outbound Exfiltration)
    - encrypted_anomaly (TLS Anomalous Session)
    """
    import uuid
    from datetime import UTC, datetime

    from schema.models import (
        EvidenceItem,
        MitreTechnique,
        SeverityLevel,
        ThreatClass,
    )

    valid_scenarios = [
        "kill_chain",
        "ddos_surge",
        "dga_c2",
        "exfil_spike",
        "encrypted_anomaly",
    ]
    if scenario not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario}'. Valid options: {valid_scenarios}",
        )

    now = datetime.now(UTC)
    simulated_alerts: list[Alert] = []
    simulated_incident: Incident | None = None

    if scenario == "kill_chain":
        a1 = Alert(
            alert_id=f"ALT-RECON-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.105",
            dst_ip="10.0.0.1",
            protocol="TCP",
            threat_class=ThreatClass.RECONNAISSANCE,
            severity=SeverityLevel.MEDIUM,
            confidence=0.89,
            risk_score=54.5,
            title="Horizontal TCP SYN Port Scan across 64 destination ports",
            evidence=[
                EvidenceItem(key="syn_ack_ratio", value="0.02"),
                EvidenceItem(key="ports_probed", value="64 ports"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1046",
                    technique_name="Network Service Discovery",
                )
            ],
        )
        a2 = Alert(
            alert_id=f"ALT-C2-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.105",
            dst_ip="198.51.100.22",
            protocol="TCP",
            threat_class=ThreatClass.C2_BEACONING,
            severity=SeverityLevel.HIGH,
            confidence=0.95,
            risk_score=79.2,
            title="Periodic C2 Beaconing session detected with low IAT variance",
            evidence=[
                EvidenceItem(key="iat_cv", value="0.07"),
                EvidenceItem(key="destination_asn", value="AS13335"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1071.004",
                    technique_name="Application Layer Protocol: DNS/C2",
                )
            ],
        )
        a3 = Alert(
            alert_id=f"ALT-EXFIL-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.105",
            dst_ip="198.51.100.22",
            protocol="TCP",
            threat_class=ThreatClass.EXFILTRATION,
            severity=SeverityLevel.CRITICAL,
            confidence=0.98,
            risk_score=94.0,
            title="Outbound Asymmetric Data Exfiltration Transfer (> 5.2 MB)",
            evidence=[
                EvidenceItem(key="byte_ratio", value="16.4"),
                EvidenceItem(key="entropy_payload", value="7.92 bits/byte"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1048",
                    technique_name="Exfiltration Over Alternative Protocol",
                )
            ],
        )
        simulated_alerts = [a1, a2, a3]

        simulated_incident = Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            title="Multi-Stage Attack Chain: Recon -> C2 -> Exfiltration",
            status="active",
            severity="critical",
            risk_score=94.5,
            created_at=now,
            last_updated=now,
            primary_host_ip="192.168.1.105",
            target_destination_ips=["198.51.100.22", "10.0.0.1"],
            alert_ids=[a.alert_id for a in simulated_alerts],
            threat_classes=["RECONNAISSANCE", "C2_BEACONING", "EXFILTRATION"],
            attack_chain="RECONNAISSANCE -> C2_BEACONING -> EXFILTRATION",
            summary=(
                "High-confidence multi-stage attack detected on host 192.168.1.105 "
                "within a 30-minute rolling graph window."
            ),
        )

    elif scenario == "ddos_surge":
        a1 = Alert(
            alert_id=f"ALT-DDOS-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.200",
            dst_ip="10.0.0.50",
            protocol="TCP",
            threat_class=ThreatClass.DDOS,
            severity=SeverityLevel.CRITICAL,
            confidence=0.96,
            risk_score=88.5,
            title="Distributed Denial of Service (SYN Flood > 15,000 pkts/s)",
            evidence=[
                EvidenceItem(key="packet_rate", value="15,420 pkts/s"),
                EvidenceItem(key="syn_flood_ratio", value="0.99"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1498.001",
                    technique_name="Network Denial of Service: Direct Flood",
                )
            ],
        )
        simulated_alerts = [a1]

    elif scenario == "dga_c2":
        a1 = Alert(
            alert_id=f"ALT-DGA-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.140",
            dst_ip="8.8.8.8",
            protocol="UDP",
            threat_class=ThreatClass.DGA,
            severity=SeverityLevel.HIGH,
            confidence=0.92,
            risk_score=76.0,
            title="Algorithmic Domain Generation (DGA Query Fluxing)",
            evidence=[
                EvidenceItem(key="domain_entropy", value="4.65 bits/char"),
                EvidenceItem(key="consonant_ratio", value="0.78"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1568.002",
                    technique_name="Dynamic Resolution: Domain Generation",
                )
            ],
        )
        simulated_alerts = [a1]

    elif scenario == "exfil_spike":
        a1 = Alert(
            alert_id=f"ALT-EXFIL-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.180",
            dst_ip="203.0.113.88",
            protocol="TCP",
            threat_class=ThreatClass.EXFILTRATION,
            severity=SeverityLevel.CRITICAL,
            confidence=0.97,
            risk_score=93.0,
            title="Anomalous Outbound Transfer Spike (+5.4σ above baseline)",
            evidence=[
                EvidenceItem(key="outbound_bytes", value="8,490,200 bytes"),
                EvidenceItem(key="baseline_sigma", value="+5.4σ"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1048",
                    technique_name="Exfiltration Over Alternative Protocol",
                )
            ],
        )
        simulated_alerts = [a1]

    elif scenario == "encrypted_anomaly":
        a1 = Alert(
            alert_id=f"ALT-ENC-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.160",
            dst_ip="198.51.100.99",
            protocol="TLS",
            threat_class=ThreatClass.ENCRYPTED_ANOMALY,
            severity=SeverityLevel.MEDIUM,
            confidence=0.88,
            risk_score=62.0,
            title="Encrypted TLS Session Anomaly: High entropy & self-signed cert",
            evidence=[
                EvidenceItem(key="tls_entropy", value="7.88 bits/byte"),
                EvidenceItem(key="sni_mismatch", value="true"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1573.002",
                    technique_name="Encrypted Channel: Asymmetric Crypto",
                )
            ],
        )
        simulated_alerts = [a1]

    # Persist and broadcast all simulated alerts
    for a in simulated_alerts:
        global_alert_store.save_alert(a)
        await broadcast_ws_message(
            {"type": "NEW_ALERT", "data": a.model_dump(mode="json")}
        )

    # Persist and broadcast simulated incident if created
    if simulated_incident:
        global_alert_store.save_incident(simulated_incident)
        await broadcast_ws_message(
            {
                "type": "NEW_INCIDENT",
                "data": simulated_incident.model_dump(mode="json"),
            }
        )

    return {
        "status": "replayed",
        "scenario": scenario,
        "alerts_generated": len(simulated_alerts),
        "incident_generated": bool(simulated_incident),
        "alerts": [a.model_dump(mode="json") for a in simulated_alerts],
        "incident": (
            simulated_incident.model_dump(mode="json")
            if simulated_incident
            else None
        ),
        "timestamp": now.isoformat(),
    }


@router.websocket("/ws/live")
async def live_dashboard_websocket(websocket: WebSocket) -> None:
    """Real-time WebSocket pushing live alerts and incidents to dashboard."""
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Initial greeting and handshake
        await websocket.send_text(
            json.dumps(
                {"type": "CONNECTED", "msg": "UDT-X Live Telemetry Stream Active"}
            )
        )
        while True:
            # Keep-alive ping loop
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG"}))
    except WebSocketDisconnect:
        connected_websockets.discard(websocket)
    except Exception as exc:
        logger.debug("WebSocket error: %s", exc)
        connected_websockets.discard(websocket)
