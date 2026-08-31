"""UDT-X DGA & DNS Tunnelling Detection Engine — Unit Tests.

Tests:
1. Shannon entropy calculation on strings.
2. Domain extraction into (subdomain, sld, tld).
3. Legitimate domain queries produce NO false positive alerts.
4. Known DGA domains trigger threat_class="DGA".
5. DNS Data Exfiltration / Tunnelling triggers threat_class="DNS_TUNNELING".
6. Evidence includes domain_entropy and ngram_score.
7. MITRE ATT&CK mappings (T1568.002 for DGA, T1048.003 / T1071.004).
8. Alert Pydantic schema validation & JSON round-trip.
"""

from __future__ import annotations

from datetime import UTC, datetime

from engines.dga_dns_tunnel.detector import (
    calculate_entropy,
    extract_domain_parts,
)
from engines.dga_dns_tunnel.worker import DGADNSTunnelEngine
from features.extractor import calculate_ngram_anomaly_score, calculate_shannon_entropy
from schema.models import (
    Alert,
    DirectionalFeatures,
    DNSFeatures,
    FeatureVector,
    FlowDirection,
    NetworkFeatures,
    TemporalFeatures,
)


def _make_dns_fv(
    query: str,
    src_ip: str = "10.0.0.50",
    dst_ip: str = "8.8.8.8",
    query_freq: int = 1,
) -> FeatureVector:
    """Build a FeatureVector populated with real DNS feature values."""
    domain_entropy = calculate_shannon_entropy(query)
    ngram_score = calculate_ngram_anomaly_score(query)
    query_len = len(query)

    return FeatureVector(
        flow_id=f"dns-flow:{src_ip}->{dst_ip}:{query}",
        timestamp=datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="UDP",
        network=NetworkFeatures(
            packets_per_sec=1.0,
            bytes_per_sec=float(query_len + 60),
            packet_size_mean=float(query_len + 60),
            window_flow_count=query_freq,
        ),
        directional=DirectionalFeatures(
            direction=FlowDirection.OUTBOUND,
            outbound_bytes_window=query_len + 60,
        ),
        temporal=TemporalFeatures(duration_ms=25.0),
        dns=DNSFeatures(
            query=query,
            query_length=query_len,
            domain_entropy=domain_entropy,
            ngram_score=ngram_score,
            dns_query_frequency_window=query_freq,
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Entropy & Parsing Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_entropy_computation() -> None:
    assert calculate_entropy("") == 0.0
    # "aaaa" has 0 entropy
    assert calculate_entropy("aaaa") == 0.0
    # High entropy for pseudo-random string
    ent = calculate_entropy("a1b2c3d4e5f6g7h8")
    assert ent > 3.5


def test_domain_parts_extraction() -> None:
    sub, sld, tld = extract_domain_parts("test.example.com")
    assert sub == "test"
    assert sld == "example"
    assert tld == "com"

    sub, sld, tld = extract_domain_parts("xqzrwpkz7941q.biz")
    assert sub == ""
    assert sld == "xqzrwpkz7941q"
    assert tld == "biz"

    sub, sld, tld = extract_domain_parts("chunk01.exfil.data.tunnelcorp.org.")
    assert sub == "chunk01.exfil.data"
    assert sld == "tunnelcorp"
    assert tld == "org"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Legitimate Domains → NO Alerts
# ─────────────────────────────────────────────────────────────────────────────


def test_legitimate_domains_no_false_positives() -> None:
    engine = DGADNSTunnelEngine(confidence_threshold=0.50, dry_run=True)

    legit_domains = [
        "google.com",
        "github.com",
        "microsoft.com",
        "amazon.co.uk",
        "wikipedia.org",
        "cloudflare.com",
        "api.twitter.com",
        "mail.google.com",
        "update.microsoft.com",
    ]

    alerts: list[Alert] = []
    for domain in legit_domains:
        fv = _make_dns_fv(query=domain)
        result = engine.process_feature_vector(fv)
        if result is not None:
            alerts.append(result)

    assert len(alerts) == 0, f"False positive on legitimate domains: {alerts}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Known DGA Domains → Alert (DGA)
# ─────────────────────────────────────────────────────────────────────────────


def test_dga_domains_trigger_alert() -> None:
    """Sample of real/synthetic DGA feed strings (Bambenek / Conficker-style)."""
    engine = DGADNSTunnelEngine(confidence_threshold=0.50, dry_run=True)

    dga_domains = [
        "xqzrwpkz7941q.biz",
        "vzkpmqtzwryxb.info",
        "hyzqwpjkmbcxz.net",
        "qwrtypsdfghjkl.ru",
    ]

    emitted_dga: list[Alert] = []
    for domain in dga_domains:
        fv = _make_dns_fv(query=domain, src_ip="10.99.1.5")
        result = engine.process_feature_vector(fv)
        if result is not None and result.threat_class == "DGA":
            emitted_dga.append(result)

    assert len(emitted_dga) >= 3, (
        f"Expected at least 3 DGA alerts, got {len(emitted_dga)}"
    )
    alert = emitted_dga[0]
    assert alert.threat_class == "DGA"
    assert any(m.technique_id == "T1568.002" for m in alert.mitre)

    # Check evidence contains domain_entropy and ngram_score
    ev_keys = {e.key for e in alert.evidence}
    assert "domain_entropy" in ev_keys
    assert "ngram_score" in ev_keys


# ─────────────────────────────────────────────────────────────────────────────
# 4. DNS Tunnelling Exfiltration → Alert (DNS_TUNNELING)
# ─────────────────────────────────────────────────────────────────────────────


def test_dns_tunneling_sequence_triggers_alert() -> None:
    """Simulate DNS exfiltration tool (e.g. iodine, dnscat2) streaming hex chunks."""
    engine = DGADNSTunnelEngine(confidence_threshold=0.50, dry_run=True)
    src_ip = "192.168.1.105"
    apex = "tunnel-c2.net"

    emitted_tunnel: list[Alert] = []
    # Emit 12 sequential unique chunks of exfiltrated data
    for i in range(12):
        chunk_hex = f"4a7f9b8c2d1e0f3a6b5c4d3e2f1a0b9c8d7e6f{i:02x}"
        query = f"{chunk_hex}.stage.{apex}"
        fv = _make_dns_fv(query=query, src_ip=src_ip, query_freq=i + 1)
        result = engine.process_feature_vector(fv)
        if result is not None and result.threat_class == "DNS_TUNNELING":
            emitted_tunnel.append(result)

    assert len(emitted_tunnel) > 0, "Expected DNS_TUNNELING alert"
    alert = emitted_tunnel[0]
    assert alert.threat_class == "DNS_TUNNELING"
    assert any(m.technique_id == "T1048.003" for m in alert.mitre)
    assert any(m.technique_id == "T1071.004" for m in alert.mitre)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Alert Schema Validation Round-Trip
# ─────────────────────────────────────────────────────────────────────────────


def test_dns_alert_schema_roundtrip() -> None:
    engine = DGADNSTunnelEngine(confidence_threshold=0.40, dry_run=True)
    fv = _make_dns_fv("hyzqwpjkmbcxz.net", src_ip="10.5.5.5")
    alert = engine.process_feature_vector(fv)

    assert alert is not None
    reloaded = Alert.model_validate_json(alert.model_dump_json())
    assert reloaded.alert_id == alert.alert_id
    assert reloaded.threat_class == "DGA"
    assert reloaded.schema_version == "1.0.0"
    assert len(reloaded.evidence) > 0
