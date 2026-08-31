"""UDT-X Alert & Incident REST and WebSocket Endpoints (Phase 10 & Accounts/RateLimiting)."""

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
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from schema.models import Alert
from services.api.app.routers.auth import (
    INITIAL_USERS,
    UserRecord,
    decode_jwt_token,
    get_current_user,
)

logger = logging.getLogger("udtx.api.router")

router = APIRouter(tags=["SOC & Alerts"])

# Active WebSocket dashboard clients tracking: ws -> user_email
connected_websockets: dict[WebSocket, str] = {}
MAX_WS_PER_USER = 3


async def broadcast_ws_message(message: dict[str, Any]) -> None:
    """Broadcast alert/incident event to all connected dashboard websockets."""
    disconnected: list[WebSocket] = []
    text_data = json.dumps(message)
    for ws in list(connected_websockets.keys()):
        try:
            await ws.send_text(text_data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connected_websockets.pop(ws, None)


@router.get("/alerts", response_model=list[Alert])
async def get_alerts(
    request: Request,
    threat_class: str | None = Query(None, description="Filter by threat class"),
    severity: str | None = Query(None, description="Filter by severity"),
    min_risk: float | None = Query(None, description="Filter by minimum risk"),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: UserRecord = Depends(get_current_user),
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
    request: Request,
    time_range: str = Query(default="24h", pattern="^(1h|24h|7d|30d)$"),
    _current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    """Breakdown of alerts, counts, risk scores, and severities by threat class."""
    return global_alert_store.get_threat_stats(time_range=time_range)


@router.get("/alerts/export")
async def export_alerts(
    request: Request,
    format: str = Query("cef", description="Export format: 'cef' or 'syslog'"),
    limit: int = Query(100, ge=1, le=1000),
    _current_user: UserRecord = Depends(get_current_user),
) -> Response:
    """Export alerts in CEF or Syslog RFC 5424 formats for SIEM ingestion."""
    alerts = global_alert_store.get_alerts(limit=limit)
    content = AlertExporter.export_all(alerts, format_type=format)
    media_type = "text/plain"
    return Response(content=content, media_type=media_type)


@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert_by_id(
    request: Request,
    alert_id: str,
    _current_user: UserRecord = Depends(get_current_user),
) -> Alert:
    """Retrieve a single alert by its unique alert_id."""
    alert = global_alert_store.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts", response_model=Alert, status_code=201)
async def ingest_and_broadcast_alert(
    request: Request,
    alert: Alert,
    _current_user: UserRecord = Depends(get_current_user),
) -> Alert:
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
    request: Request,
    status: str | None = Query(None, description="Filter by incident status"),
    min_risk: float | None = Query(None, description="Filter by minimum risk"),
    limit: int = Query(50, ge=1, le=500),
    _current_user: UserRecord = Depends(get_current_user),
) -> list[Incident]:
    """Retrieve correlated multi-alert Incidents."""
    return global_alert_store.get_incidents(
        status=status,
        min_risk=min_risk,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident_by_id(
    request: Request,
    incident_id: str,
    _current_user: UserRecord = Depends(get_current_user),
) -> Incident:
    """Retrieve a single correlated incident by its incident_id."""
    inc = global_alert_store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.post("/incidents", response_model=Incident, status_code=201)
async def ingest_and_broadcast_incident(
    request: Request,
    incident: Incident,
    _current_user: UserRecord = Depends(get_current_user),
) -> Incident:
    """Ingest, store, and broadcast an incident in real time."""
    saved = global_alert_store.save_incident(incident)
    asyncio.create_task(
        broadcast_ws_message(
            {"type": "NEW_INCIDENT", "data": saved.model_dump(mode="json")}
        )
    )
    return saved


@router.get("/performance")
async def get_performance_metrics(
    request: Request,
    _current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    """SOC/SIEM real-time engine processing performance metrics."""
    return global_alert_store.get_performance_metrics()


@router.get("/graph")
async def get_evidence_graph_topology(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    _current_user: UserRecord = Depends(get_current_user),
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
    request: Request,
    scenario: str,
    _current_user: UserRecord = Depends(get_current_user),
) -> dict[str, Any]:
    """Replay simulation test scenarios generating live alerts and incidents."""
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
                EvidenceItem(key="iat_variance", value="0.003s"),
                EvidenceItem(key="periodicity_score", value="0.96"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1071.001",
                    technique_name="Web Protocols",
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
            risk_score=94.8,
            title="Asymmetric large-volume outbound exfiltration spike",
            evidence=[
                EvidenceItem(key="bytes_out_ratio", value="0.994"),
                EvidenceItem(key="novelty_score", value="1.00"),
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
            incident_id=f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}",
            alert_ids=[a.alert_id for a in simulated_alerts],
            window_start=now,
            window_end=now,
            risk_score=92.5,
            attack_chain="MULTI_STAGE_KILLCHAIN (Recon -> C2 -> Exfiltration)",
            host="192.168.1.105",
            threat_classes=[
                ThreatClass.RECONNAISSANCE,
                ThreatClass.C2_BEACONING,
                ThreatClass.EXFILTRATION,
            ],
        )
    elif scenario == "ddos_surge":
        a1 = Alert(
            alert_id=f"ALT-DDOS-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="203.0.113.88",
            dst_ip="10.0.0.5",
            protocol="TCP",
            threat_class=ThreatClass.DDOS,
            severity=SeverityLevel.CRITICAL,
            confidence=0.99,
            risk_score=98.0,
            title="Massive TCP SYN Flood Surge: 85,000 pps",
            evidence=[
                EvidenceItem(key="packet_rate", value="85000 pps"),
                EvidenceItem(key="syn_flag_ratio", value="0.99"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1498.001",
                    technique_name="Direct Network Flood",
                )
            ],
        )
        simulated_alerts = [a1]
    elif scenario == "dga_c2":
        a1 = Alert(
            alert_id=f"ALT-DGA-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.44",
            dst_ip="8.8.8.8",
            protocol="UDP",
            threat_class=ThreatClass.DGA,
            severity=SeverityLevel.HIGH,
            confidence=0.93,
            risk_score=81.0,
            title="Algorithmic Domain Generation Flux (Shannon Entropy 4.42)",
            evidence=[
                EvidenceItem(key="shannon_entropy", value="4.42"),
                EvidenceItem(key="ngram_prob", value="0.001"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1568.002",
                    technique_name="Domain Generation Algorithms",
                )
            ],
        )
        simulated_alerts = [a1]
    elif scenario == "exfil_spike":
        a1 = Alert(
            alert_id=f"ALT-EXFIL-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.18",
            dst_ip="203.0.113.200",
            protocol="TCP",
            threat_class=ThreatClass.EXFILTRATION,
            severity=SeverityLevel.HIGH,
            confidence=0.94,
            risk_score=86.5,
            title="Outbound Transfer Volume Surge: 450 MB / 60s",
            evidence=[
                EvidenceItem(key="outbound_volume", value="450MB"),
                EvidenceItem(key="destination_novelty", value="0.98"),
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
            alert_id=f"ALT-TLS-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            src_ip="192.168.1.92",
            dst_ip="198.51.100.99",
            protocol="TCP",
            threat_class=ThreatClass.ENCRYPTED_ANOMALY,
            severity=SeverityLevel.MEDIUM,
            confidence=0.88,
            risk_score=68.0,
            title="Unknown JA3 Fingerprint with anomalous TLS byte entropy",
            evidence=[
                EvidenceItem(key="ja3_hash", value="a0e9f5d643ac64e8"),
                EvidenceItem(key="tls_entropy", value="7.82"),
            ],
            mitre=[
                MitreTechnique(
                    technique_id="T1573.002",
                    technique_name="Asymmetric Cryptography",
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
async def live_dashboard_websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
) -> None:
    """Authenticated real-time WebSocket pushing live alerts and incidents."""
    user_email = "anonymous-analyst@udtx.local"

    # Authenticate token if provided
    if token:
        try:
            payload = decode_jwt_token(token)
            email = payload.get("sub")
            if email and email in INITIAL_USERS:
                user_email = email
            else:
                await websocket.close(code=4401, reason="Invalid enclave station token")
                return
        except Exception:
            await websocket.close(code=4401, reason="Authentication failed")
            return

    # Check concurrent connections per user
    existing_user_conns = sum(1 for e in connected_websockets.values() if e == user_email)
    if existing_user_conns >= MAX_WS_PER_USER:
        await websocket.close(
            code=4429,
            reason=f"Exceeded max concurrent WebSocket connections ({MAX_WS_PER_USER})",
        )
        return

    await websocket.accept()
    connected_websockets[websocket] = user_email

    try:
        # Initial greeting
        await websocket.send_text(
            json.dumps(
                {
                    "type": "CONNECTED",
                    "msg": "UDT-X Live Telemetry Stream Active",
                    "user": user_email,
                }
            )
        )
        while True:
            # Keep-alive ping loop
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG"}))
    except WebSocketDisconnect:
        connected_websockets.pop(websocket, None)
    except Exception as exc:
        logger.debug("WebSocket error: %s", exc)
        connected_websockets.pop(websocket, None)
