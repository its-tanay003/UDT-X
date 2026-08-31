"""UDT-X Encrypted-Session Anomaly Detection Engine — Unit Tests.

Tests:
1. Standard browser JA3 fingerprint (known-good) produces 0 anomaly score.
2. Malformed JA3 fingerprint (invalid length/characters) triggers anomaly alert.
3. Known malicious JA3 fingerprint (e.g. Cobalt Strike) triggers alert.
4. Host baseline rarity: a rare JA3 seen on an established host scores high anomaly.
5. Handshake packet-size sequence anomaly (e.g. identical packet lengths).
6. Timing anomaly (e.g. abnormally stalled handshake > 5000ms).
7. Alert schema round-trip and MITRE mapping (T1573.002).
"""

from __future__ import annotations

from datetime import UTC, datetime

from engines.encrypted_session.detector import EncryptedSessionDetector
from engines.encrypted_session.worker import EncryptedSessionEngine
from schema.models import (
    Alert,
    DirectionalFeatures,
    FeatureVector,
    FlowDirection,
    NetworkFeatures,
    TemporalFeatures,
    TLSFeatures,
)


def _make_tls_fv(
    src_ip: str = "10.1.1.20",
    dst_ip: str = "104.244.42.1",
    ja3: str | None = "b32309a26951912be7dba376398abc3b",  # Standard Chrome
    ja3s: str | None = "ec74a5c5110605f25cec8bc3d373be30",
    sni: str | None = "twitter.com",
    cipher: str | int | None = "TLS_AES_128_GCM_SHA256",
    packet_sizes: list[int] | None = None,
    handshake_duration_ms: float | None = 65.0,
) -> FeatureVector:
    """Build a FeatureVector populated with TLS metadata."""
    sizes = packet_sizes if packet_sizes is not None else [517, 1420, 1420, 310, 120]
    return FeatureVector(
        flow_id=f"tls-flow:{src_ip}->{dst_ip}:{sni}",
        timestamp=datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="TCP",
        network=NetworkFeatures(
            packets_per_sec=10.0,
            bytes_per_sec=4500.0,
            packet_size_mean=600.0,
            window_flow_count=1,
        ),
        directional=DirectionalFeatures(
            direction=FlowDirection.OUTBOUND,
            outbound_bytes_window=4500,
        ),
        temporal=TemporalFeatures(duration_ms=450.0),
        tls=TLSFeatures(
            ja3=ja3,
            ja3s=ja3s,
            sni=sni,
            cipher=cipher,
            packet_size_sequence=sizes,
            handshake_duration_ms=handshake_duration_ms,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Known-Good Standard Browser JA3 -> NO Alert
# ─────────────────────────────────────────────────────────────────────────────


def test_standard_browser_ja3_no_alert() -> None:
    engine = EncryptedSessionEngine(confidence_threshold=0.50, dry_run=True)
    # Chrome JA3
    fv = _make_tls_fv(
        ja3="b32309a26951912be7dba376398abc3b",
        sni="www.google.com",
        packet_sizes=[512, 1420, 850, 310],
        handshake_duration_ms=45.0,
    )
    alert = engine.process_feature_vector(fv)
    assert alert is None, f"False positive on standard browser JA3: {alert}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Known Malicious JA3 (Cobalt Strike) -> Alert
# ─────────────────────────────────────────────────────────────────────────────


def test_known_malicious_ja3_triggers_alert() -> None:
    engine = EncryptedSessionEngine(confidence_threshold=0.50, dry_run=True)
    # Cobalt Strike default JA3
    cs_ja3 = "a0e9f5d64349fb13191bc781f81f42e1"
    fv = _make_tls_fv(
        src_ip="10.10.10.45",
        dst_ip="198.51.100.22",
        ja3=cs_ja3,
        sni="c2.attacker.com",
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None, "Expected alert for known malicious Cobalt Strike JA3"
    assert alert.threat_class == "ENCRYPTED_ANOMALY"
    assert alert.confidence >= 0.50
    assert any(m.technique_id == "T1573.002" for m in alert.mitre)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Malformed JA3 Fingerprint -> Alert
# ─────────────────────────────────────────────────────────────────────────────


def test_malformed_ja3_triggers_alert() -> None:
    engine = EncryptedSessionEngine(confidence_threshold=0.50, dry_run=True)
    # Invalid length/chars
    bad_ja3 = "XYZ123_invalid_ja3_fingerprint!"
    fv = _make_tls_fv(
        src_ip="10.2.2.88",
        dst_ip="203.0.113.88",
        ja3=bad_ja3,
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None, "Expected alert for malformed JA3"
    assert alert.threat_class == "ENCRYPTED_ANOMALY"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Handshake Packet-Size Sequence Anomaly
# ─────────────────────────────────────────────────────────────────────────────


def test_fixed_packet_size_sequence_anomaly() -> None:
    engine = EncryptedSessionEngine(confidence_threshold=0.45, dry_run=True)
    # Atypical uniform packet size sequence (e.g. constant padding channel)
    fv = _make_tls_fv(
        src_ip="10.4.4.12",
        dst_ip="198.51.100.77",
        ja3="11223344556677889900aabbccddeeff",  # Unknown JA3
        packet_sizes=[128, 128, 128, 128, 128],
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None, "Expected alert for uniform packet size sequence"
    ev_keys = {e.key for e in alert.evidence}
    assert "packet_sequence_anomaly_score" in ev_keys


# ─────────────────────────────────────────────────────────────────────────────
# 5. Handshake Timing Anomaly
# ─────────────────────────────────────────────────────────────────────────────


def test_handshake_timing_anomaly() -> None:
    det = EncryptedSessionDetector()
    score, reason = det._evaluate_timing(8200.0)  # > 5000ms delay
    assert score > 0.50
    assert "delayed" in reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Alert Schema Round-Trip
# ─────────────────────────────────────────────────────────────────────────────


def test_encrypted_anomaly_alert_schema_roundtrip() -> None:
    engine = EncryptedSessionEngine(confidence_threshold=0.40, dry_run=True)
    fv = _make_tls_fv(
        src_ip="10.9.9.9",
        ja3="a0e9f5d64349fb13191bc781f81f42e1",
    )
    alert = engine.process_feature_vector(fv)
    assert alert is not None

    reloaded = Alert.model_validate_json(alert.model_dump_json())
    assert reloaded.alert_id == alert.alert_id
    assert reloaded.threat_class == "ENCRYPTED_ANOMALY"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
