"""UDT-X C2 Beaconing Detection Engine — Unit Tests.

Tests:
1.  Periodicity signal returns 0.0 for aperiodic flows.
2.  Periodicity signal returns high score for strict beacon (high periodicity,
    near-zero jitter).
3.  High jitter dampens the periodicity sub-score even when periodicity_score is high.
4.  Persistence score is zero before threshold contacts are reached.
5.  Persistence score rises toward 1.0 with many contacts over a long window.
6.  Payload score is high for tiny / consistent beacon packets.
7.  Payload score is near zero for normal large-payload HTTP responses.
8.  Synthetic fixed-interval beacon → Alert emitted with threat_class="C2_BEACONING".
9.  Synthetic legitimate polling service (HTTP health-check) → NO false positive.
10. Alert evidence includes periodicity_score and persistence_score.
11. Alert MITRE mapping includes T1071.
12. Alert Pydantic schema round-trip survives JSON serialisation.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from engines.c2_beacon.detector import C2BeaconDetector, PersistenceTracker
from engines.c2_beacon.worker import C2BeaconEngine
from schema.models import (
    Alert,
    DirectionalFeatures,
    FeatureVector,
    FlowDirection,
    NetworkFeatures,
    TemporalFeatures,
)

# ─────────────────────────────────────────────────────────────────────────────
# FeatureVector factory
# ─────────────────────────────────────────────────────────────────────────────


def _make_fv(
    src_ip: str = "10.0.0.1",
    dst_ip: str = "203.0.113.50",
    protocol: str = "TCP",
    periodicity: float = 0.0,
    jitter_ms: float = 200.0,
    pkt_mean: float = 500.0,
    pkt_stddev: float = 50.0,
    bps: float = 5_000.0,
    duration_ms: float = 100.0,
    ts: datetime | None = None,
) -> FeatureVector:
    return FeatureVector(
        flow_id=f"c2-test:{src_ip}:{dst_ip}",
        timestamp=ts or datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        network=NetworkFeatures(
            packets_per_sec=bps / max(pkt_mean, 1.0),
            bytes_per_sec=bps,
            packet_size_mean=pkt_mean,
            packet_size_stddev=pkt_stddev,
            window_flow_count=1,
            window_unique_dst_ips=1,
            window_unique_dst_ports=1,
        ),
        directional=DirectionalFeatures(
            direction=FlowDirection.OUTBOUND,
            outbound_bytes_window=int(bps * duration_ms / 1000),
            inbound_bytes_window=0,
        ),
        temporal=TemporalFeatures(
            duration_ms=duration_ms,
            inter_arrival_time_ms=30_000.0,
            jitter_ms=jitter_ms,
            periodicity_score=periodicity,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Aperiodic flow → periodicity signal = 0
# ─────────────────────────────────────────────────────────────────────────────


def test_periodicity_signal_zero_for_aperiodic() -> None:
    det = C2BeaconDetector()
    sig = det._periodicity_signal(periodicity_score=0.20, jitter_ms=500.0)
    assert sig == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Strict beacon → periodicity signal near 1.0
# ─────────────────────────────────────────────────────────────────────────────


def test_periodicity_signal_high_for_strict_beacon() -> None:
    det = C2BeaconDetector()
    # periodicity_score=0.95, jitter=2 ms → should be close to 1.0
    sig = det._periodicity_signal(periodicity_score=0.95, jitter_ms=2.0)
    assert sig >= 0.80, f"Expected signal ≥ 0.80, got {sig}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. High jitter dampens periodicity sub-score
# ─────────────────────────────────────────────────────────────────────────────


def test_high_jitter_dampens_periodicity_signal() -> None:
    det = C2BeaconDetector()
    low_jitter = det._periodicity_signal(periodicity_score=0.90, jitter_ms=5.0)
    high_jitter = det._periodicity_signal(periodicity_score=0.90, jitter_ms=480.0)
    assert low_jitter > high_jitter, (
        f"Low-jitter signal ({low_jitter:.3f}) should exceed "
        f"high-jitter signal ({high_jitter:.3f})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Persistence score is 0 before threshold
# ─────────────────────────────────────────────────────────────────────────────


def test_persistence_score_zero_before_threshold() -> None:
    tracker = PersistenceTracker()
    t0 = time.monotonic()
    for i in range(3):  # below CONTACT_LOW=5
        tracker.observe("10.0.0.1", "203.0.113.1", now=t0 + i * 30)
    score = tracker.score("10.0.0.1", "203.0.113.1")
    assert score == 0.0, f"Expected 0.0 below contact threshold, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Persistence score rises with contacts + long window
# ─────────────────────────────────────────────────────────────────────────────


def test_persistence_score_rises_with_contacts_and_time() -> None:
    tracker = PersistenceTracker()
    t0 = time.monotonic()
    for i in range(25):  # 25 contacts over 15 min
        tracker.observe("10.0.0.1", "203.0.113.2", now=t0 + i * 36.0)
    score = tracker.score("10.0.0.1", "203.0.113.2")
    assert score >= 0.70, f"Expected persistence ≥ 0.70, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Payload score high for tiny / consistent packets
# ─────────────────────────────────────────────────────────────────────────────


def test_payload_score_high_for_beacon_sized_packets() -> None:
    det = C2BeaconDetector()
    # 60-byte mean, stddev 2 bytes → CV = 0.033
    score = det._payload_signal(packet_size_mean=60.0, packet_size_stddev=2.0)
    assert score >= 0.70, f"Expected payload ≥ 0.70 for beacon packets, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Payload score near zero for large HTTP responses
# ─────────────────────────────────────────────────────────────────────────────


def test_payload_score_low_for_http_responses() -> None:
    det = C2BeaconDetector()
    # 1200-byte mean (full MTU-ish), stddev 200 bytes → CV = 0.17
    # With PAYLOAD_BYTES_HIGH=300 the size_factor = 0 at 1200 B
    # CV=0.17 is between CV_LOW=0.05 and CV_HIGH=0.35, giving partial cv_factor
    # Total score = 0 * 0.65 + partial * 0.35 ≈ 0.18 < 0.25
    score = det._payload_signal(packet_size_mean=1_200.0, packet_size_stddev=200.0)
    assert score < 0.25, f"Expected payload < 0.25 for HTTP traffic, got {score}"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Synthetic fixed-interval C2 beacon → Alert emitted
# ─────────────────────────────────────────────────────────────────────────────


def test_fixed_interval_beacon_triggers_alert() -> None:
    """
    Simulate a C2 implant beaconing every 30 s with ±2 ms jitter.

    Profile:
    - periodicity_score = 0.95  (autocorrelation near-perfect)
    - jitter_ms = 3             (strict timer, OS scheduling only)
    - packet_size_mean = 80     (keep-alive / checkin payload)
    - packet_size_stddev = 3    (very consistent)
    - 30 contacts spaced 30 s apart (15-minute total window)
    """
    engine = C2BeaconEngine(confidence_threshold=0.50, dry_run=True)
    src, dst = "10.10.0.5", "198.51.100.25"
    t0 = time.monotonic()
    emitted: list[Alert] = []

    for i in range(30):
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            protocol="TCP",
            periodicity=0.95,
            jitter_ms=3.0,
            pkt_mean=80.0,
            pkt_stddev=3.0,
            bps=80.0 * 2.0 / 30.0,
        )
        result = engine.process_feature_vector(fv, now=t0 + i * 30.0)
        if result is not None:
            emitted.append(result)

    assert len(emitted) > 0, (
        "Expected at least one C2_BEACONING alert after 30 contacts; "
        f"last confidence was "
        f"{engine.detector.tracker.score(src, dst):.3f}"
    )
    alert = emitted[0]
    assert alert.threat_class == "C2_BEACONING"
    assert alert.confidence >= 0.50
    assert alert.src_ip == src
    assert alert.dst_ip == dst


# ─────────────────────────────────────────────────────────────────────────────
# 9. Legitimate polling service → NO false positive
# ─────────────────────────────────────────────────────────────────────────────


def test_legitimate_polling_service_no_false_positive() -> None:
    """
    Simulate a Kubernetes liveness probe / Prometheus scraper:
    - Polls every 15 s with 300 ms jitter (network + app-server RTT variance)
    - Returns a full HTTP/200 JSON body (~650 bytes)
    - Accesses a known internal endpoint

    Key differentiators vs C2:
    ✓ High jitter (300 ms > JITTER_MAX_MS=250) → jitter_factor = 0
      → periodicity sub-score is dampened to its 0.70 component only
    ✓ Large payload (650 B > PAYLOAD_BYTES_HIGH=300) → size_factor = 0
    ✓ Composite stays below 0.50 threshold
    """
    engine = C2BeaconEngine(confidence_threshold=0.50, dry_run=True)
    src, dst = "10.20.0.1", "10.20.0.99"  # internal service
    t0 = time.monotonic()
    alerts: list[Alert] = []

    for i in range(30):
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            protocol="TCP",
            periodicity=0.82,  # high regularity (scrape interval timer)
            jitter_ms=300.0,  # 300 ms > JITTER_MAX(250) → jitter_factor=0
            pkt_mean=800.0,  # large JSON response body
            pkt_stddev=200.0,  # highly variable (gzip, metadata)
            bps=800.0 * 4.0 / 15.0,
        )
        result = engine.process_feature_vector(fv, now=t0 + i * 15.0)
        if result is not None:
            alerts.append(result)

    assert len(alerts) == 0, (
        f"False positive: {len(alerts)} C2_BEACONING alert(s) for legitimate "
        f"polling service. First confidence: "
        f"{alerts[0].confidence if alerts else 'N/A'}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. Alert evidence contains required keys
# ─────────────────────────────────────────────────────────────────────────────


def test_alert_evidence_contains_required_keys() -> None:
    engine = C2BeaconEngine(confidence_threshold=0.40, dry_run=True)
    src, dst = "10.0.0.7", "198.51.100.77"
    t0 = time.monotonic()
    last: Alert | None = None

    for i in range(30):
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            periodicity=0.93,
            jitter_ms=4.0,
            pkt_mean=75.0,
            pkt_stddev=4.0,
        )
        result = engine.process_feature_vector(fv, now=t0 + i * 60.0)
        if result is not None:
            last = result

    assert last is not None, "Expected at least one alert for evidence check"
    ev_keys = {e.key for e in last.evidence}
    assert "periodicity_score" in ev_keys, "Missing periodicity_score in evidence"
    assert "persistence_score" in ev_keys, "Missing persistence_score in evidence"
    assert "contact_count" in ev_keys, "Missing contact_count in evidence"
    assert "jitter_ms" in ev_keys, "Missing jitter_ms in evidence"


# ─────────────────────────────────────────────────────────────────────────────
# 11. MITRE T1071 mapping present
# ─────────────────────────────────────────────────────────────────────────────


def test_alert_mitre_includes_t1071() -> None:
    engine = C2BeaconEngine(confidence_threshold=0.40, dry_run=True)
    src, dst = "10.0.0.8", "198.51.100.88"
    t0 = time.monotonic()
    last: Alert | None = None

    for i in range(30):
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            periodicity=0.93,
            jitter_ms=5.0,
            pkt_mean=80.0,
            pkt_stddev=5.0,
        )
        result = engine.process_feature_vector(fv, now=t0 + i * 30.0)
        if result is not None:
            last = result

    assert last is not None
    assert any(m.technique_id == "T1071" for m in last.mitre), (
        "Expected MITRE T1071 mapping in C2 alert"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 12. Alert JSON round-trip
# ─────────────────────────────────────────────────────────────────────────────


def test_alert_schema_roundtrip() -> None:
    engine = C2BeaconEngine(confidence_threshold=0.40, dry_run=True)
    src, dst = "10.0.0.9", "198.51.100.99"
    t0 = time.monotonic()
    last: Alert | None = None

    for i in range(30):
        fv = _make_fv(
            src_ip=src,
            dst_ip=dst,
            periodicity=0.95,
            jitter_ms=3.0,
            pkt_mean=78.0,
            pkt_stddev=3.0,
        )
        result = engine.process_feature_vector(fv, now=t0 + i * 30.0)
        if result is not None:
            last = result

    assert last is not None
    reloaded = Alert.model_validate_json(last.model_dump_json())
    assert reloaded.alert_id == last.alert_id
    assert reloaded.threat_class == "C2_BEACONING"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
    assert len(reloaded.mitre) >= 1
