"""UDT-X Threat Intelligence & MITRE Mapping — Unit Tests.

Tests:
1. MITRE technique mapping for all canonical threat classes.
2. Local offline IOC match annotates alert and elevates confidence & risk score.
3. Fail-open behavior: Missing/non-existent IOC feed file still enriches MITRE
   and successfully emits alert without crashing.
4. Fail-open behavior: Missing MITRE map file still passes raw alert through.
5. End-to-end streaming worker process.
"""

from __future__ import annotations

from datetime import UTC, datetime

from intel.enricher import ThreatIntelEnricher
from intel.worker import IntelEnrichmentService
from schema.models import Alert, EvidenceItem, SeverityLevel


def _make_sample_alert(
    threat_class: str = "C2_BEACONING",
    src_ip: str = "192.168.1.50",
    dst_ip: str = "198.51.100.77",
) -> Alert:
    return Alert(
        alert_id="alt-test-01",
        timestamp=datetime.now(UTC),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="TCP",
        threat_class=threat_class,
        severity=SeverityLevel.HIGH,
        confidence=0.80,
        risk_score=70.0,
        evidence=[
            EvidenceItem(
                key="PERIODICITY_SCORE",
                value="0.95",
                context={"jitter_ms": 1.2},
            )
        ],
        mitre=[],
        title=f"Sample {threat_class}",
    )


def test_mitre_mapping_for_threat_classes() -> None:
    enricher = ThreatIntelEnricher(
        mitre_map_path="intel/mitre_map.json",
        ioc_feed_path=None,
    )

    classes_to_test = [
        ("DDOS", "T1498"),
        ("C2_BEACONING", "T1071"),
        ("DGA", "T1568.002"),
        ("DNS_TUNNELING", "T1048.003"),
        ("ENCRYPTED_ANOMALY", "T1573.002"),
        ("RECONNAISSANCE", "T1046"),
        ("EXFILTRATION", "T1048"),
    ]

    for tc, expected_tech in classes_to_test:
        raw_alt = _make_sample_alert(threat_class=tc, dst_ip="10.0.0.1")
        enriched = enricher.enrich_alert(raw_alt)
        tech_ids = [m.technique_id for m in enriched.mitre]
        assert expected_tech in tech_ids, (
            f"Expected {expected_tech} for {tc}, got: {tech_ids}"
        )


def test_local_ioc_matching_and_risk_elevation() -> None:
    enricher = ThreatIntelEnricher(
        mitre_map_path="intel/mitre_map.json",
        ioc_feed_path="intel/data/sample_iocs.json",
    )

    # Destination matches Cobalt Strike IOC 198.51.100.77
    alert = _make_sample_alert(dst_ip="198.51.100.77")
    enriched = enricher.enrich_alert(alert)

    # Check evidence for IOC match
    evidence_keys = [e.key for e in enriched.evidence]
    assert "IOC_MATCH" in evidence_keys
    assert enriched.confidence >= 0.95
    assert enriched.risk_score >= 85.0

    ioc_item = next(e for e in enriched.evidence if e.key == "IOC_MATCH")
    assert ioc_item.value == "198.51.100.77"
    assert ioc_item.context["threat_actor"] == "APT29 / Cozy Bear"


def test_fail_open_when_ioc_feed_missing() -> None:
    """Core Requirement: If optional IOC list is missing or fails to load,

    the service must still pass through alerts with MITRE mapping only.
    """
    enricher = ThreatIntelEnricher(
        mitre_map_path="intel/mitre_map.json",
        ioc_feed_path="non/existent/path/to/missing_iocs.json",
    )

    raw_alert = _make_sample_alert(threat_class="EXFILTRATION")
    enriched = enricher.enrich_alert(raw_alert)

    # Alert must NOT be dropped, and MITRE techniques must be present
    assert enriched is not None
    assert enriched.alert_id == raw_alert.alert_id
    assert len(enriched.mitre) >= 1
    assert any(m.technique_id == "T1048" for m in enriched.mitre)
    # No IOC evidence item added
    assert not any(e.key == "IOC_MATCH" for e in enriched.evidence)


def test_fail_open_when_mitre_map_missing() -> None:
    """If MITRE map is absent, raw alert still passes through safely."""
    enricher = ThreatIntelEnricher(
        mitre_map_path="non/existent/mitre_map.json",
        ioc_feed_path=None,
    )

    raw_alert = _make_sample_alert(threat_class="RECONNAISSANCE")
    enriched = enricher.enrich_alert(raw_alert)

    assert enriched is not None
    assert enriched.alert_id == raw_alert.alert_id


def test_streaming_service_end_to_end() -> None:
    service = IntelEnrichmentService(
        mitre_map_path="intel/mitre_map.json",
        ioc_feed_path="intel/data/sample_iocs.json",
        dry_run=True,
    )

    raw_alert = _make_sample_alert(threat_class="DDOS", dst_ip="198.51.100.77")
    res = service.process_alert(raw_alert)

    assert res.alert_id == raw_alert.alert_id
    assert any(m.technique_id == "T1498" for m in res.mitre)
    assert any(e.key == "IOC_MATCH" for e in res.evidence)
