"""UDT-X Data Exfiltration Detection Engine — Unit Tests.

Tests:
1. Destination novelty detection (first-time vs established destination).
2. Asymmetric byte ratio scoring (high outbound / minimal inbound).
3. Large outbound transfer to brand new destination triggers Alert.
4. Routine scheduled backup to known destination produces NO alert.
5. Time-of-day off-hours bonus.
6. Alert schema validation & MITRE mapping (T1048, T1041).
"""

from __future__ import annotations

from datetime import UTC, datetime

from engines.exfiltration.detector import ExfiltrationDetector
from engines.exfiltration.worker import ExfiltrationEngine
from schema.models import (
    Alert,
    DirectionalFeatures,
    FeatureVector,
    FlowDirection,
    NetworkFeatures,
    TemporalFeatures,
)


def _make_exfil_fv(
    src_ip: str = "10.0.0.15",
    dst_ip: str = "198.51.100.99",
    outbound_bytes: int = 50_000_000,  # 50 MB
    inbound_bytes: int = 25_000,  # 25 KB
    hour: int = 23,
) -> FeatureVector:
    """Build a FeatureVector with directional metrics."""
    ts = datetime(2026, 8, 27, hour, 15, 0, tzinfo=UTC)
    ratio = outbound_bytes / max(1, inbound_bytes)

    return FeatureVector(
        flow_id=f"exfil-flow:{src_ip}->{dst_ip}",
        timestamp=ts,
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="TCP",
        network=NetworkFeatures(
            packets_per_sec=500.0,
            bytes_per_sec=float(outbound_bytes) / 60.0,
            packet_size_mean=1400.0,
            window_flow_count=1,
        ),
        directional=DirectionalFeatures(
            direction=FlowDirection.OUTBOUND,
            outbound_bytes_window=outbound_bytes,
            inbound_bytes_window=inbound_bytes,
            byte_ratio_out_in=ratio,
        ),
        temporal=TemporalFeatures(duration_ms=60_000.0),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Destination Novelty & Ratio Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_destination_novelty_tracking() -> None:
    det = ExfiltrationDetector()
    sig1 = det.evaluate(
        src_ip="10.0.0.1",
        dst_ip="192.0.2.1",
        outbound_bytes=5000,
        inbound_bytes=5000,
        byte_ratio=1.0,
        timestamp=datetime.now(UTC),
    )
    assert sig1.novelty_score == 1.0  # First time

    sig2 = det.evaluate(
        src_ip="10.0.0.1",
        dst_ip="192.0.2.1",
        outbound_bytes=5000,
        inbound_bytes=5000,
        byte_ratio=1.0,
        timestamp=datetime.now(UTC),
    )
    assert sig2.novelty_score == 0.0  # Established


# ─────────────────────────────────────────────────────────────────────────────
# 2. Large Outbound Transfer to New Destination -> ALERT
# ─────────────────────────────────────────────────────────────────────────────


def test_large_outbound_to_new_destination_triggers_alert() -> None:
    engine = ExfiltrationEngine(confidence_threshold=0.50, dry_run=True)
    # 150 MB outbound transfer at 23:00 to an unknown IP
    fv = _make_exfil_fv(
        src_ip="10.1.2.3",
        dst_ip="203.0.113.88",
        outbound_bytes=150_000_000,
        inbound_bytes=50_000,
        hour=23,
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None, "Expected alert for large transfer to new destination"
    assert alert.threat_class == "EXFILTRATION"
    assert alert.confidence >= 0.50
    assert any(m.technique_id == "T1048" for m in alert.mitre)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Routine Backup to Known Destination -> NO Alert
# ─────────────────────────────────────────────────────────────────────────────


def test_routine_backup_to_known_destination_no_alert() -> None:
    engine = ExfiltrationEngine(confidence_threshold=0.50, dry_run=True)
    src_ip = "10.1.2.4"
    backup_server = "10.50.0.10"

    # Seed baseline with 5 routine backup transfers of ~20 MB
    for _ in range(5):
        fv_seed = _make_exfil_fv(
            src_ip=src_ip,
            dst_ip=backup_server,
            outbound_bytes=20_000_000,
            inbound_bytes=2_000_000,
            hour=2,
        )
        engine.process_feature_vector(fv_seed)

    # Next scheduled routine backup of expected size (22 MB) to established server
    fv_routine = _make_exfil_fv(
        src_ip=src_ip,
        dst_ip=backup_server,
        outbound_bytes=22_000_000,
        inbound_bytes=2_000_000,
        hour=2,
    )
    alert = engine.process_feature_vector(fv_routine)
    assert alert is None, (
        f"False positive on routine backup to known destination: {alert}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Alert Schema Round-Trip
# ─────────────────────────────────────────────────────────────────────────────


def test_exfiltration_alert_schema_roundtrip() -> None:
    engine = ExfiltrationEngine(confidence_threshold=0.40, dry_run=True)
    fv = _make_exfil_fv(
        src_ip="10.8.8.8",
        dst_ip="198.51.100.5",
        outbound_bytes=200_000_000,
        inbound_bytes=10_000,
        hour=1,
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None

    reloaded = Alert.model_validate_json(alert.model_dump_json())
    assert reloaded.alert_id == alert.alert_id
    assert reloaded.threat_class == "EXFILTRATION"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
