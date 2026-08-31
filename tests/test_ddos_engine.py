"""UDT-X DDoS Detection Engine — Unit Tests.

Tests:
1. EWMA tracker z-score calculation during warmup and after spike.
2. Entropy window Shannon entropy and collapse detection.
3. Traffic spike sequence → high confidence, alert emitted.
4. Benign burst sequence  → low confidence, no false-positive alert.
5. UDP flood ratio → protocol_score escalation.
6. Alert Pydantic model integrity (evidence[], mitre[], schema_version).
"""

from __future__ import annotations

from datetime import UTC, datetime

from engines.ddos.detector import DDoSDetector, EntropyWindow, EWMATracker
from engines.ddos.worker import DDoSEngine
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
    protocol: str = "UDP",
    pps: float = 1000.0,
    bps: float = 500_000.0,
    window_flow_count: int = 1,
    direction: FlowDirection = FlowDirection.INBOUND,
    ts: datetime | None = None,
) -> FeatureVector:
    return FeatureVector(
        flow_id=f"test-{src_ip}-{pps}",
        timestamp=ts or datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        network=NetworkFeatures(
            packets_per_sec=pps,
            bytes_per_sec=bps,
            window_flow_count=window_flow_count,
            window_unique_dst_ips=1,
            window_unique_dst_ports=1,
        ),
        directional=DirectionalFeatures(
            direction=direction,
            outbound_bytes_window=0,
            inbound_bytes_window=int(bps),
        ),
        temporal=TemporalFeatures(duration_ms=1000.0),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. EWMA Tracker
# ─────────────────────────────────────────────────────────────────────────────


def test_ewma_warmup_returns_zero() -> None:
    """Z-score must be 0 during warm-up period."""
    tracker = EWMATracker(alpha=0.2, warmup=5)
    for _ in range(4):
        z = tracker.update(100.0)
        assert z == 0.0


def test_ewma_spike_produces_positive_zscore() -> None:
    """A large spike after stable baseline must produce a high positive z-score."""
    tracker = EWMATracker(alpha=0.2, warmup=5)
    # Stable baseline
    for _ in range(10):
        tracker.update(100.0)
    # Large spike
    z = tracker.update(10_000.0)
    assert z > 3.0, f"Expected z > 3.0, got {z}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Entropy Window
# ─────────────────────────────────────────────────────────────────────────────


def test_entropy_single_source_is_zero() -> None:
    """One repeated IP → entropy = 0."""
    w = EntropyWindow()
    for _ in range(20):
        w.add("1.2.3.4")
    assert w.entropy() == 0.0


def test_entropy_many_sources_is_high() -> None:
    """Many unique IPs → entropy should be > 4 bits."""
    w = EntropyWindow()
    for i in range(64):
        w.add(f"10.0.{i // 256}.{i % 256}")
    assert w.entropy() > 4.0


def test_entropy_collapse_detected() -> None:
    """
    After entropy window is filled by 1 source, entropy_score should be > 0
    once we have at least 4 unique sources registered first, then converge.
    """
    detector = DDoSDetector(dst_ip="192.0.2.10", warmup_samples=3)

    # Seed with 4 distinct IPs to pass the uniqueness gate
    for i in range(4):
        detector.src_entropy_window.add(f"10.0.0.{i + 1}")

    # Then flood with 50 copies of a single IP (simulating amplification)
    for _ in range(50):
        detector.src_entropy_window.add("10.0.0.1")

    score = detector._entropy_score("10.0.0.1")
    assert score > 0.0, f"Expected entropy_score > 0, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. DDoS Traffic Spike → Alert Emitted
# ─────────────────────────────────────────────────────────────────────────────


def test_ddos_spike_sequence_triggers_alert() -> None:
    """
    Synthetic volumetric DDoS: 5 baseline samples then 10 spike samples
    from many source IPs → confidence must exceed 0.50 and alert emitted.
    """
    engine = DDoSEngine(
        confidence_threshold=0.50,
        warmup_samples=5,
        dry_run=True,
    )

    dst = "192.0.2.100"

    # Phase 1: Warm up with normal traffic (100 pps, 50KB/s)
    for i in range(5):
        fv = _make_fv(src_ip=f"10.1.0.{i + 1}", dst_ip=dst, pps=100.0, bps=50_000.0)
        engine.process_feature_vector(fv)

    # Phase 2: DDoS spike — 50 000 pps, 500 MB/s from many sources
    alert_emitted: Alert | None = None
    for i in range(10):
        fv = _make_fv(
            src_ip=f"203.0.{i}.{i + 1}",  # many different attacker IPs
            dst_ip=dst,
            protocol="UDP",
            pps=50_000.0 + i * 1000,
            bps=500_000_000.0 + i * 1_000_000,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            alert_emitted = result

    assert alert_emitted is not None, "Expected at least one DDoS alert to be emitted"
    assert alert_emitted.threat_class == "DDOS"
    assert alert_emitted.confidence >= 0.50
    assert alert_emitted.dst_ip == dst
    assert len(alert_emitted.evidence) > 0
    assert any(m.technique_id == "T1498" for m in alert_emitted.mitre)
    assert alert_emitted.schema_version == "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Legitimate Traffic Burst → No False Positive
# ─────────────────────────────────────────────────────────────────────────────


def test_benign_burst_does_not_trigger_alert() -> None:
    """
    A legitimate flash crowd or short-lived traffic burst within 3× of
    baseline must NOT generate a DDoS alert (no false positive).
    """
    engine = DDoSEngine(
        confidence_threshold=0.50,
        warmup_samples=5,
        dry_run=True,
    )

    dst = "192.0.2.200"

    # Establish a moderate baseline
    for i in range(8):
        fv = _make_fv(
            src_ip=f"10.2.0.{i + 1}",
            dst_ip=dst,
            protocol="TCP",
            pps=500.0,
            bps=250_000.0,
        )
        engine.process_feature_vector(fv)

    # Legitimate burst: 2× baseline, TCP, from one IP — should NOT alert
    alerts: list[Alert] = []
    for _i in range(5):
        fv = _make_fv(
            src_ip="10.2.0.1",  # single known source
            dst_ip=dst,
            protocol="TCP",
            pps=1_000.0,  # 2× baseline — within normal headroom
            bps=500_000.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            alerts.append(result)

    assert len(alerts) == 0, (
        f"False positive: {len(alerts)} alert(s) emitted for benign burst. "
        f"confidence={engine._detectors.get(dst)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. UDP Flood Protocol Score
# ─────────────────────────────────────────────────────────────────────────────


def test_udp_flood_raises_protocol_score() -> None:
    """Pure UDP traffic stream must escalate protocol_score > 0.5."""
    detector = DDoSDetector(dst_ip="10.0.0.1", warmup_samples=3)

    for _i in range(10):
        detector._protocol_score("UDP", pps=5000.0)

    score = detector._protocol_score("UDP", pps=5000.0)
    assert score > 0.5, f"Expected protocol_score > 0.5, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Alert Schema Integrity
# ─────────────────────────────────────────────────────────────────────────────


def test_alert_model_roundtrip() -> None:
    """Emitted Alert must survive JSON round-trip and pass Pydantic validation."""
    engine = DDoSEngine(confidence_threshold=0.30, warmup_samples=3, dry_run=True)
    dst = "198.51.100.5"

    for i in range(3):
        fv = _make_fv(src_ip=f"10.9.0.{i + 1}", dst_ip=dst, pps=80.0, bps=40_000.0)
        engine.process_feature_vector(fv)

    alert_out: Alert | None = None
    for i in range(8):
        fv = _make_fv(
            src_ip=f"10.9.{i}.1",
            dst_ip=dst,
            protocol="UDP",
            pps=100_000.0,
            bps=1_000_000_000.0,
        )
        result = engine.process_feature_vector(fv)
        if result is not None:
            alert_out = result
            break

    assert alert_out is not None
    # Round-trip through JSON
    raw_json = alert_out.model_dump_json()
    reloaded = Alert.model_validate_json(raw_json)
    assert reloaded.alert_id == alert_out.alert_id
    assert reloaded.threat_class == "DDOS"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
    assert len(reloaded.mitre) >= 1
