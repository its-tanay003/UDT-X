"""UDT-X Reconnaissance Detection Engine — Unit Tests.

Tests:
1. PortHistory.sequentiality_score returns 1.0 for purely sequential ports.
2. PortHistory.sequentiality_score returns 0.0 for widely-spaced random ports.
3. Fan-out score scales correctly: low (< LOW_MARK) → 0, high (> HIGH_MARK) → 1.
4. Probe signature activates on tiny-packet / high-conn flows.
5. Probe signature stays quiet on normal flows.
6. Port-scan sequence → confidence > threshold, Alert emitted.
7. Normal multi-service client → confidence < threshold, no false positive.
8. Host-sweep (many unique dst IPs, varied ports) → Alert emitted.
9. Alert Pydantic schema round-trip: threat_class, evidence[], mitre[].
"""

from __future__ import annotations

from datetime import UTC, datetime

from engines.recon.detector import PortHistory, ReconDetector
from engines.recon.worker import ReconEngine
from schema.models import (
    Alert,
    DirectionalFeatures,
    FeatureVector,
    FlowDirection,
    NetworkFeatures,
    TemporalFeatures,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_fv(
    src_ip: str = "10.0.0.1",
    dst_ip: str = "192.0.2.10",
    dst_port: int = 80,
    protocol: str = "TCP",
    pps: float = 10.0,
    bps: float = 2_000.0,
    unique_dst_ips: int = 1,
    unique_dst_ports: int = 1,
    flow_count: int = 1,
    pkt_size_mean: float = 200.0,
    duration_ms: float = 100.0,
    ts: datetime | None = None,
) -> FeatureVector:
    """Build a minimal FeatureVector with port encoded in flow_id."""
    return FeatureVector(
        flow_id=f"recon-test:{src_ip}:{dst_port}",
        timestamp=ts or datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        network=NetworkFeatures(
            packets_per_sec=pps,
            bytes_per_sec=bps,
            packet_size_mean=pkt_size_mean,
            packet_size_stddev=pkt_size_mean * 0.1,
            window_flow_count=flow_count,
            window_unique_dst_ips=unique_dst_ips,
            window_unique_dst_ports=unique_dst_ports,
        ),
        directional=DirectionalFeatures(
            direction=FlowDirection.OUTBOUND,
            outbound_bytes_window=int(bps * duration_ms / 1000),
            inbound_bytes_window=0,
        ),
        temporal=TemporalFeatures(duration_ms=duration_ms),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Sequentiality Score — pure sequential
# ─────────────────────────────────────────────────────────────────────────────


def test_sequentiality_score_pure_sequential() -> None:
    """1, 2, 3, 4, 5 → sequentiality = 1.0."""
    ph = PortHistory()
    for p in range(1, 10):
        ph.add(p, "192.0.2.1")
    assert ph.sequentiality_score() == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Sequentiality Score — random normal ports
# ─────────────────────────────────────────────────────────────────────────────


def test_sequentiality_score_random_ports() -> None:
    """Widely-spaced service ports → sequentiality near 0."""
    ph = PortHistory()
    # Typical web-client ports
    for p in [80, 443, 22, 8080, 3306, 5432, 6379, 27017]:
        ph.add(p, "192.0.2.2")
    score = ph.sequentiality_score()
    assert score < 0.20, f"Expected low sequentiality, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Fan-out score scaling
# ─────────────────────────────────────────────────────────────────────────────


def test_fanout_score_below_low_mark_is_zero() -> None:
    """unique_dst_ports = 3 (< LOW_MARK=8) → fanout_score = 0."""
    det = ReconDetector(src_ip="10.0.0.1")
    score = det._fanout_score(unique_dst_ips=1, unique_dst_ports=3)
    assert score == 0.0


def test_fanout_score_above_high_mark_is_one() -> None:
    """unique_dst_ips = 40 (> HIGH_MARK=30) → fanout_score = 1.0."""
    det = ReconDetector(src_ip="10.0.0.2")
    score = det._fanout_score(unique_dst_ips=40, unique_dst_ports=5)
    assert score == 1.0


def test_fanout_score_midpoint() -> None:
    """Midpoint between LOW and HIGH → score ≈ 0.5."""
    det = ReconDetector(src_ip="10.0.0.3")
    # DST_PORT_FANOUT_LOW=8, HIGH=50 → mid=29
    score = det._fanout_score(unique_dst_ips=1, unique_dst_ports=29)
    assert 0.40 < score < 0.60, f"Expected ~0.5 at midpoint, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Probe signature — tiny packets + many connections
# ─────────────────────────────────────────────────────────────────────────────


def test_probe_score_activates_for_syn_probe_traffic() -> None:
    """40-byte packets, 50 connections → probe_score > 0.5."""
    det = ReconDetector(src_ip="10.0.0.4")
    score = det._probe_score(
        bytes_per_flow=40.0,  # SYN-sized packet
        window_flow_count=50,
        packet_size_mean=40.0,
    )
    assert score > 0.5, f"Expected probe_score > 0.5, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Probe signature — normal traffic is quiet
# ─────────────────────────────────────────────────────────────────────────────


def test_probe_score_quiet_for_normal_http_traffic() -> None:
    """1400-byte packets, 3 flows → probe_score near 0."""
    det = ReconDetector(src_ip="10.0.0.5")
    score = det._probe_score(
        bytes_per_flow=1_400.0,  # Full MTU frames
        window_flow_count=3,
        packet_size_mean=1_400.0,
    )
    assert score < 0.20, f"Expected low probe_score, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Port-scan sequence → Alert emitted
# ─────────────────────────────────────────────────────────────────────────────


def test_port_scan_sequence_triggers_alert() -> None:
    """
    Nmap-style TCP SYN scan: src hits 40 sequential ports on a single host,
    each with a tiny 40-byte flow. Confidence must exceed threshold.
    """
    engine = ReconEngine(confidence_threshold=0.45, dry_run=True)
    src = "10.99.0.1"
    dst = "192.0.2.50"
    emitted: list[Alert] = []

    for port in range(1, 41):  # ports 1–40: sequential scan
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            dst_port=port,
            protocol="TCP",
            pps=5.0,
            bps=200.0,  # 40 B/flow * 5 flows/s
            unique_dst_ips=1,
            unique_dst_ports=port,  # grows monotonically as scan progresses
            flow_count=port,
            pkt_size_mean=40.0,  # SYN-only packets
            duration_ms=10.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            emitted.append(result)

    assert len(emitted) > 0, "Expected at least one RECONNAISSANCE alert"
    alert = emitted[0]
    assert alert.threat_class == "RECONNAISSANCE"
    assert alert.confidence >= 0.45
    assert alert.src_ip == src

    # Evidence must carry fan-out and scan-rate
    ev_keys = {e.key for e in alert.evidence}
    assert "fan_out_count" in ev_keys
    assert "scan_rate" in ev_keys
    assert "sequentiality_score" in ev_keys

    # MITRE T1046 must be mapped
    assert any(m.technique_id == "T1046" for m in alert.mitre)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Normal multi-service client → no false positive
# ─────────────────────────────────────────────────────────────────────────────


def test_normal_multi_service_client_no_false_positive() -> None:
    """
    A developer laptop connecting to HTTPS, SSH, Postgres, Redis, and a REST
    API on 5 different hosts. Traffic is large (HTTP responses), few connections.
    Must NOT trigger a Recon alert.
    """
    engine = ReconEngine(confidence_threshold=0.45, dry_run=True)
    src = "10.1.0.100"

    normal_services = [
        ("10.10.0.1", 443, "TCP", 5_000.0, 1_400.0, 2),  # HTTPS
        ("10.10.0.2", 22, "TCP", 3_000.0, 1_200.0, 1),  # SSH
        ("10.10.0.3", 5432, "TCP", 8_000.0, 1_450.0, 3),  # PostgreSQL
        ("10.10.0.4", 6379, "TCP", 2_000.0, 500.0, 1),  # Redis
        ("10.10.0.5", 8080, "TCP", 10_000.0, 1_400.0, 4),  # REST API
    ]
    alerts: list[Alert] = []
    for dst, port, proto, bps, pkt_mean, flows in normal_services:
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            dst_port=port,
            protocol=proto,
            pps=bps / pkt_mean,
            bps=bps,
            unique_dst_ips=len(alerts) + 1,  # grows, but stays small
            unique_dst_ports=len(alerts) + 1,
            flow_count=flows,
            pkt_size_mean=pkt_mean,
            duration_ms=500.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            alerts.append(result)

    assert len(alerts) == 0, (
        f"False positive: {len(alerts)} RECON alert(s) for normal client. "
        f"First: {alerts[0].confidence if alerts else 'N/A'}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. Host sweep → Alert emitted
# ─────────────────────────────────────────────────────────────────────────────


def test_host_sweep_triggers_alert() -> None:
    """
    ICMP / TCP ping sweep of 35 distinct hosts on the same port (port 445 SMB).
    Fan-out score alone should push confidence over threshold.
    """
    engine = ReconEngine(confidence_threshold=0.45, dry_run=True)
    src = "172.16.0.5"
    emitted: list[Alert] = []

    for i in range(1, 36):  # 35 unique destination hosts
        fv = _make_fv(
            src_ip=src,
            dst_ip=f"10.0.1.{i}",
            dst_port=445,
            protocol="TCP",
            pps=2.0,
            bps=80.0,
            unique_dst_ips=i,  # host count climbs
            unique_dst_ports=1,  # always same port → host sweep
            flow_count=i,
            pkt_size_mean=40.0,
            duration_ms=20.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            emitted.append(result)

    assert len(emitted) > 0, "Expected host-sweep alert"
    alert = emitted[0]
    assert alert.threat_class == "RECONNAISSANCE"
    assert alert.src_ip == src


# ─────────────────────────────────────────────────────────────────────────────
# 9. Alert schema round-trip
# ─────────────────────────────────────────────────────────────────────────────


def test_alert_schema_roundtrip() -> None:
    """Alert must survive JSON round-trip and pass Pydantic validation."""
    engine = ReconEngine(confidence_threshold=0.40, dry_run=True)
    src = "10.200.0.1"
    last_alert: Alert | None = None

    for port in range(1, 55):
        fv = _make_fv(
            src_ip=src,
            dst_ip="192.0.2.200",
            dst_port=port,
            protocol="TCP",
            pps=3.0,
            bps=120.0,
            unique_dst_ips=1,
            unique_dst_ports=port,
            flow_count=port,
            pkt_size_mean=40.0,
            duration_ms=10.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            last_alert = result

    assert last_alert is not None
    reloaded = Alert.model_validate_json(last_alert.model_dump_json())
    assert reloaded.alert_id == last_alert.alert_id
    assert reloaded.threat_class == "RECONNAISSANCE"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
    assert len(reloaded.mitre) >= 1
    assert any(m.technique_id == "T1595" for m in reloaded.mitre)
