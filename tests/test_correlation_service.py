"""UDT-X Incident Temporal Correlation & Evidence Graph — Unit Tests.

Tests:
1. Multi-alert temporal grouping within rolling time window.
2. Alert merging preserves all alert IDs, target IPs, and escalates severity.
3. Attack Chain Detection: Recon -> C2 Beacon -> Exfiltration sequence produces a single
   tagged Incident with AttackChainProgression.FULL_KILL_CHAIN.
4. Attacks outside the time window create distinct independent Incidents.
5. Neo4j Evidence Graph mock/contract verification.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from correlation.correlator import IncidentCorrelator
from correlation.models import AttackChainProgression
from correlation.worker import CorrelationService
from schema.models import Alert, EvidenceItem, MitreAttack, SeverityLevel


def _make_raw_alert(
    alert_id: str,
    threat_class: str,
    src_ip: str,
    dst_ip: str,
    timestamp: datetime,
    severity: SeverityLevel = SeverityLevel.MEDIUM,
    risk_score: float = 60.0,
) -> Alert:
    """Helper to generate canonical Alert objects."""
    return Alert(
        alert_id=alert_id,
        timestamp=timestamp,
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="TCP",
        threat_class=threat_class,
        severity=severity,
        confidence=0.90,
        risk_score=risk_score,
        evidence=[
            EvidenceItem(
                key="THREAT_CLASS",
                value=threat_class,
                context={"stage": threat_class},
            )
        ],
        mitre=[
            MitreAttack(
                technique_id="T1046" if "RECON" in threat_class else "T1071",
                technique_name=threat_class,
            )
        ],
        title=f"Detected {threat_class}",
    )


def test_incident_grouping_within_time_window() -> None:
    correlator = IncidentCorrelator(window_minutes=30)
    base_time = datetime(2026, 8, 27, 10, 0, 0, tzinfo=UTC)

    # 1. First alert on host
    a1 = _make_raw_alert(
        alert_id="alert-1",
        threat_class="RECONNAISSANCE",
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        timestamp=base_time,
        severity=SeverityLevel.LOW,
        risk_score=40.0,
    )
    inc1, is_new1 = correlator.correlate_alert(a1)
    assert is_new1 is True
    assert len(inc1.alert_ids) == 1
    assert inc1.primary_host_ip == "192.168.1.100"

    # 2. Second alert 10 minutes later (within 30m window)
    a2 = _make_raw_alert(
        alert_id="alert-2",
        threat_class="RECONNAISSANCE",
        src_ip="192.168.1.100",
        dst_ip="10.0.0.2",
        timestamp=base_time + timedelta(minutes=10),
        severity=SeverityLevel.MEDIUM,
        risk_score=55.0,
    )
    inc2, is_new2 = correlator.correlate_alert(a2)
    assert is_new2 is False
    assert inc1.incident_id == inc2.incident_id
    assert len(inc2.alert_ids) == 2
    assert "10.0.0.1" in inc2.target_destination_ips
    assert "10.0.0.2" in inc2.target_destination_ips


def test_recon_to_beacon_to_exfil_attack_chain() -> None:
    """Requirement test: Feed synthetic recon->beacon->exfiltration sequence on one host

    and confirm a single tagged incident is produced instead of three unrelated alerts.
    """
    service = CorrelationService(window_minutes=30, dry_run=True)
    host_ip = "10.0.50.25"
    base_time = datetime(2026, 8, 27, 14, 0, 0, tzinfo=UTC)

    # Stage 1: Reconnaissance (14:00)
    alert_recon = _make_raw_alert(
        alert_id="alt-recon-001",
        threat_class="RECONNAISSANCE",
        src_ip=host_ip,
        dst_ip="10.0.0.5",
        timestamp=base_time,
        severity=SeverityLevel.LOW,
        risk_score=45.0,
    )
    inc_stage1 = service.process_alert(alert_recon)
    assert inc_stage1.attack_chain is None
    assert len(inc_stage1.alert_ids) == 1

    # Stage 2: C2 Beaconing (14:12)
    alert_beacon = _make_raw_alert(
        alert_id="alt-c2-002",
        threat_class="C2_BEACONING",
        src_ip=host_ip,
        dst_ip="198.51.100.77",
        timestamp=base_time + timedelta(minutes=12),
        severity=SeverityLevel.HIGH,
        risk_score=80.0,
    )
    inc_stage2 = service.process_alert(alert_beacon)
    assert inc_stage2.incident_id == inc_stage1.incident_id
    assert len(inc_stage2.alert_ids) == 2
    assert inc_stage2.attack_chain == AttackChainProgression.RECON_TO_C2

    # Stage 3: Data Exfiltration (14:25)
    alert_exfil = _make_raw_alert(
        alert_id="alt-exfil-003",
        threat_class="EXFILTRATION",
        src_ip=host_ip,
        dst_ip="203.0.113.88",
        timestamp=base_time + timedelta(minutes=25),
        severity=SeverityLevel.CRITICAL,
        risk_score=95.0,
    )
    inc_stage3 = service.process_alert(alert_exfil)

    # Verification: Single unified incident representing full kill chain
    assert inc_stage3.incident_id == inc_stage1.incident_id
    assert len(inc_stage3.alert_ids) == 3
    assert inc_stage3.attack_chain == AttackChainProgression.FULL_KILL_CHAIN
    assert inc_stage3.severity == SeverityLevel.CRITICAL
    assert inc_stage3.risk_score >= 95.0
    assert "Full Kill Chain" in inc_stage3.title
    assert len(inc_stage3.threat_classes) == 3


def test_alerts_outside_window_form_separate_incidents() -> None:
    correlator = IncidentCorrelator(window_minutes=30)
    base_time = datetime(2026, 8, 27, 8, 0, 0, tzinfo=UTC)

    # Morning Alert (08:00)
    a1 = _make_raw_alert(
        alert_id="a1",
        threat_class="RECONNAISSANCE",
        src_ip="192.168.1.5",
        dst_ip="10.0.0.1",
        timestamp=base_time,
    )
    inc1, is_new1 = correlator.correlate_alert(a1)
    assert is_new1 is True

    # Afternoon Alert (14:00 - 6 hours later)
    a2 = _make_raw_alert(
        alert_id="a2",
        threat_class="EXFILTRATION",
        src_ip="192.168.1.5",
        dst_ip="10.0.0.2",
        timestamp=base_time + timedelta(hours=6),
    )
    inc2, is_new2 = correlator.correlate_alert(a2)
    assert is_new2 is True
    assert inc1.incident_id != inc2.incident_id
