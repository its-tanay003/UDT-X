"""Unit tests for Zeek and Suricata log adapters."""

from ingestion.suricata_adapter.adapter import (
    parse_suricata_alert_record,
    parse_suricata_flow_record,
)
from ingestion.zeek_adapter.adapter import parse_zeek_conn_record
from schema.models import Alert, FlowEvent, FlowSource, SeverityLevel


def test_zeek_conn_record_parsing() -> None:
    """Verify parsing a Zeek conn.log JSON record."""
    zeek_raw = {
        "ts": 1724670000.123,
        "uid": "CAbc1234567890",
        "id.orig_h": "192.168.1.20",
        "id.orig_p": 49152,
        "id.resp_h": "1.1.1.1",
        "id.resp_p": 53,
        "proto": "udp",
        "service": "dns",
        "duration": 0.045,
        "orig_bytes": 60,
        "resp_bytes": 120,
        "orig_pkts": 1,
        "resp_pkts": 1,
        "local_orig": True,
        "local_resp": False,
        "query": "malware.download.net",
    }

    event = parse_zeek_conn_record(zeek_raw)
    assert event is not None
    assert isinstance(event, FlowEvent)
    assert event.flow_id == "CAbc1234567890"
    assert event.src_ip == "192.168.1.20"
    assert event.dst_ip == "1.1.1.1"
    assert event.src_port == 49152
    assert event.dst_port == 53
    assert event.protocol == "UDP"
    assert event.bytes == 180
    assert event.packets == 2
    assert event.duration_ms == 45.0
    assert event.source == FlowSource.ZEEK
    assert event.dns is not None
    assert event.dns.query == "malware.download.net"


def test_suricata_flow_record_parsing() -> None:
    """Verify parsing a Suricata eve.json flow event."""
    suricata_flow_raw = {
        "timestamp": "2026-08-26T12:00:00.123456+00:00",
        "flow_id": 9876543210,
        "event_type": "flow",
        "src_ip": "10.10.10.5",
        "src_port": 50000,
        "dest_ip": "10.10.10.6",
        "dest_port": 22,
        "proto": "TCP",
        "flow": {
            "pkts_toserver": 10,
            "pkts_toclient": 12,
            "bytes_toserver": 800,
            "bytes_toclient": 1200,
            "age": 5.2,
        },
    }

    event = parse_suricata_flow_record(suricata_flow_raw)
    assert event is not None
    assert isinstance(event, FlowEvent)
    assert event.src_ip == "10.10.10.5"
    assert event.dst_ip == "10.10.10.6"
    assert event.src_port == 50000
    assert event.dst_port == 22
    assert event.protocol == "TCP"
    assert event.bytes == 2000
    assert event.packets == 22
    assert event.duration_ms == 5200.0
    assert event.source == FlowSource.SURICATA


def test_suricata_alert_record_parsing() -> None:
    """Verify parsing a Suricata eve.json signature alert event."""
    suricata_alert_raw = {
        "timestamp": "2026-08-26T12:05:00.000000+00:00",
        "flow_id": 1122334455,
        "event_type": "alert",
        "src_ip": "192.168.1.150",
        "src_port": 44444,
        "dest_ip": "198.51.100.99",
        "dest_port": 443,
        "proto": "TCP",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 2010999,
            "rev": 1,
            "signature": "ET MALWARE Suspicious Inbound Cobalt Strike Beacon",
            "category": "A Network Trojan was detected",
            "severity": 1,  # Maps to HIGH
            "metadata": {
                "mitre_technique_id": ["T1071.001", "T1041"],
            },
        },
    }

    alert = parse_suricata_alert_record(suricata_alert_raw)
    assert alert is not None
    assert isinstance(alert, Alert)
    assert alert.src_ip == "192.168.1.150"
    assert alert.dst_ip == "198.51.100.99"
    assert alert.severity == SeverityLevel.HIGH
    assert len(alert.evidence) >= 2
    assert len(alert.mitre) == 2
    assert alert.mitre[0].technique_id == "T1071.001"
