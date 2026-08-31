"""Unit tests for UDT-X Canonical FlowEvent and Alert Schemas."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schema.models import (
    Alert,
    AlertStatus,
    DNSData,
    EvidenceItem,
    FlowDirection,
    FlowEvent,
    FlowSource,
    MitreAttack,
    SeverityLevel,
    TLSData,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


# ==============================================================================
# JSON Schema File Integrity Tests
# ==============================================================================
def test_flow_event_schema_file_exists_and_is_valid_json() -> None:
    """Ensure flow_event.schema.json exists and is valid JSON."""
    schema_file = SCHEMA_DIR / "flow_event.schema.json"
    assert schema_file.exists(), f"Schema file not found at {schema_file}"

    with open(schema_file, encoding="utf-8") as f:
        data = json.load(f)

    assert data["title"] == "FlowEvent"
    assert "properties" in data
    assert "required" in data
    assert "flow_id" in data["properties"]
    assert "src_ip" in data["properties"]
    assert "dst_ip" in data["properties"]


def test_alert_schema_file_exists_and_is_valid_json() -> None:
    """Ensure alert.schema.json exists and is valid JSON."""
    schema_file = SCHEMA_DIR / "alert.schema.json"
    assert schema_file.exists(), f"Schema file not found at {schema_file}"

    with open(schema_file, encoding="utf-8") as f:
        data = json.load(f)

    assert data["title"] == "Alert"
    assert "properties" in data
    assert "required" in data
    assert "alert_id" in data["properties"]
    assert "confidence" in data["properties"]
    assert "risk_score" in data["properties"]
    assert "evidence" in data["properties"]
    assert "mitre" in data["properties"]


# ==============================================================================
# FlowEvent Pydantic Validation Tests
# ==============================================================================
def test_valid_minimal_flow_event() -> None:
    """Test instantiating FlowEvent with minimal required valid attributes."""
    payload = {
        "flow_id": "flow-12345",
        "timestamp": "2026-08-26T12:00:00Z",
        "src_ip": "192.168.1.50",
        "dst_ip": "10.0.0.1",
        "src_port": 54321,
        "dst_port": 443,
        "protocol": "tcp",
        "direction": "outbound",
        "bytes": 1024,
        "packets": 12,
        "duration_ms": 150.5,
        "source": "zeek",
        "schema_version": "1.0.0",
    }
    event = FlowEvent(**payload)
    assert event.flow_id == "flow-12345"
    assert event.src_ip == "192.168.1.50"
    assert event.dst_ip == "10.0.0.1"
    assert event.src_port == 54321
    assert event.dst_port == 443
    assert event.protocol == "TCP"  # normalized to uppercase
    assert event.direction == FlowDirection.OUTBOUND
    assert event.bytes == 1024
    assert event.packets == 12
    assert event.duration_ms == 150.5
    assert event.source == FlowSource.ZEEK
    assert event.dns is None
    assert event.tls is None


def test_valid_full_flow_event_with_dns_and_tls() -> None:
    """Test full FlowEvent with nested DNS and TLS telemetry data."""
    payload = {
        "flow_id": "flow-full-999",
        "timestamp": "2026-08-26T12:05:00Z",
        "src_ip": "2001:db8::1",  # IPv6
        "dst_ip": "2001:db8::2",  # IPv6
        "src_port": 49152,
        "dst_port": 853,
        "protocol": "udp",
        "direction": "internal",
        "bytes": 5000,
        "packets": 40,
        "duration_ms": 230.0,
        "source": "suricata",
        "dns": {
            "query": "malicious-c2-domain.xyz",
            "qtype": "TXT",
            "entropy": 4.82,
        },
        "tls": {
            "ja3": "771,49195-49199-49196-49200,0-10-11,23-24,0",
            "ja3s": "771,49195,0",
            "sni": "c2.stealth-exfil.org",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "packet_size_sequence": [128, 512, 1024, 64],
        },
        "schema_version": "1.0.0",
    }
    event = FlowEvent(**payload)
    assert event.protocol == "UDP"
    assert event.source == FlowSource.SURICATA
    assert isinstance(event.dns, DNSData)
    assert event.dns.query == "malicious-c2-domain.xyz"
    assert event.dns.entropy == 4.82
    assert isinstance(event.tls, TLSData)
    assert event.tls.sni == "c2.stealth-exfil.org"
    assert event.tls.packet_size_sequence == [128, 512, 1024, 64]


@pytest.mark.parametrize(
    "invalid_payload, expected_err",
    [
        (
            {"src_ip": "999.999.999.999"},  # invalid IP
            "Invalid IP address format",
        ),
        (
            {"src_port": 70000},  # port > 65535
            "less than or equal to 65535",
        ),
        (
            {"dst_port": -1},  # port < 0
            "greater than or equal to 0",
        ),
        (
            {"bytes": -10},  # negative bytes
            "greater than or equal to 0",
        ),
        (
            {"packets": -1},  # negative packets
            "greater than or equal to 0",
        ),
        (
            {"duration_ms": -5.0},  # negative duration
            "greater than or equal to 0",
        ),
        (
            {"source": "invalid_collector"},  # invalid enum
            "Input should be 'pcap', 'netflow', 'ipfix', 'sflow', 'zeek' or 'suricata'",
        ),
    ],
)
def test_invalid_flow_event_payloads(invalid_payload: dict, expected_err: str) -> None:
    """Verify validation errors on corrupted flow event fields."""
    base_valid = {
        "flow_id": "flow-001",
        "timestamp": "2026-08-26T12:00:00Z",
        "src_ip": "10.0.0.2",
        "dst_ip": "10.0.0.3",
        "src_port": 80,
        "dst_port": 8080,
        "protocol": "TCP",
        "direction": "internal",
        "bytes": 100,
        "packets": 2,
        "duration_ms": 10.0,
        "source": "pcap",
    }
    base_valid.update(invalid_payload)

    with pytest.raises(ValidationError) as exc_info:
        FlowEvent(**base_valid)
    assert expected_err in str(exc_info.value)


# ==============================================================================
# Alert Pydantic Validation Tests (Section 11)
# ==============================================================================
def test_valid_alert_payload() -> None:
    """Test constructing a complete valid Alert object per Section 11."""
    payload = {
        "alert_id": "alert-c2-001",
        "timestamp": "2026-08-26T12:30:00Z",
        "flow_id": "flow-c2-999",
        "src_ip": "192.168.1.100",
        "dst_ip": "198.51.100.25",
        "protocol": "TCP",
        "threat_class": "c2_beaconing",
        "severity": "critical",
        "confidence": 0.96,
        "risk_score": 92.5,
        "evidence": [
            {
                "key": "periodicity_fft_score",
                "value": 0.985,
                "threshold": 0.85,
                "description": "High regularity FFT beaconing pattern across 120s",
            },
            {
                "key": "ja3_hash",
                "value": "e7d705a3286e19ea42f587b344ee6865",
                "threshold": "known_malicious_c2",
                "description": "Cobalt Strike malleable C2 TLS fingerprint",
            },
        ],
        "mitre": [
            {
                "tactic": "Command and Control",
                "technique_id": "T1071.001",
                "technique_name": "Web Protocols",
                "url": "https://attack.mitre.org/techniques/T1071/001/",
            },
            {
                "tactic": "Exfiltration",
                "technique_id": "T1041",
                "technique_name": "Exfiltration Over C2 Channel",
                "url": "https://attack.mitre.org/techniques/T1041/",
            },
        ],
        "title": "Cobalt Strike C2 Beaconing Detected",
        "description": "Host 192.168.1.100 exhibits persistent periodic beaconing.",
        "status": "open",
        "schema_version": "1.0.0",
    }
    alert = Alert(**payload)
    assert alert.alert_id == "alert-c2-001"
    assert alert.severity == SeverityLevel.CRITICAL
    assert alert.confidence == 0.96
    assert alert.risk_score == 92.5
    assert len(alert.evidence) == 2
    assert isinstance(alert.evidence[0], EvidenceItem)
    assert alert.evidence[0].key == "periodicity_fft_score"
    assert len(alert.mitre) == 2
    assert isinstance(alert.mitre[0], MitreAttack)
    assert alert.mitre[0].technique_id == "T1071.001"
    assert alert.status == AlertStatus.OPEN


@pytest.mark.parametrize(
    "invalid_alert, expected_err",
    [
        (
            {"confidence": 1.5},  # confidence > 1.0
            "less than or equal to 1",
        ),
        (
            {"confidence": -0.1},  # confidence < 0.0
            "greater than or equal to 0",
        ),
        (
            {"risk_score": 150.0},  # risk_score > 100.0
            "less than or equal to 100",
        ),
        (
            {"risk_score": -10.0},  # risk_score < 0.0
            "greater than or equal to 0",
        ),
        (
            {"severity": "extreme_danger"},  # invalid severity
            "Input should be 'info', 'low', 'medium', 'high' or 'critical'",
        ),
        (
            {"src_ip": "not_an_ip"},  # invalid source IP
            "Invalid IP address format",
        ),
    ],
)
def test_invalid_alert_payloads(invalid_alert: dict, expected_err: str) -> None:
    """Verify validation errors on malformed alert payloads."""
    base_valid = {
        "alert_id": "alert-test-01",
        "timestamp": "2026-08-26T12:00:00Z",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "protocol": "TCP",
        "threat_class": "port_scan",
        "severity": "medium",
        "confidence": 0.8,
        "risk_score": 60.0,
        "evidence": [],
        "mitre": [],
    }
    base_valid.update(invalid_alert)

    with pytest.raises(ValidationError) as exc_info:
        Alert(**base_valid)
    assert expected_err in str(exc_info.value)
