"""Unit tests for UDT-X Flow Normalizer and Dead Letter Queue (DLQ)."""

from normalizer.transformer import transform_to_flow_event
from normalizer.worker import FlowNormalizerWorker
from schema.models import FlowDirection, FlowEvent, FlowSource


# ==============================================================================
# Source-Specific Normalization Tests
# ==============================================================================
def test_normalize_pcap_record() -> None:
    """Test normalizing a raw PCAP flow dictionary."""
    pcap_raw = {
        "flow_id": "pcap-flow-001",
        "timestamp": "2026-08-26T12:00:00Z",
        "src_ip": "192.168.1.50",
        "dst_ip": "93.184.216.34",
        "src_port": 50000,
        "dst_port": 80,
        "protocol": "tcp",
        "direction": "outbound",
        "bytes": 2048,
        "packets": 16,
        "duration_ms": 250.0,
        "source": "pcap",
    }
    event = transform_to_flow_event(pcap_raw)
    assert isinstance(event, FlowEvent)
    assert event.flow_id == "pcap-flow-001"
    assert event.src_ip == "192.168.1.50"
    assert event.dst_ip == "93.184.216.34"
    assert event.protocol == "TCP"
    assert event.direction == FlowDirection.OUTBOUND
    assert event.bytes == 2048
    assert event.source == FlowSource.PCAP


def test_normalize_zeek_record() -> None:
    """Test normalizing a native Zeek conn.log JSON record."""
    zeek_raw = {
        "ts": 1724670000.5,
        "uid": "CZeeK123456",
        "id.orig_h": "10.0.0.15",
        "id.orig_p": 49152,
        "id.resp_h": "1.1.1.1",
        "id.resp_p": 53,
        "proto": "udp",
        "orig_bytes": 100,
        "resp_bytes": 350,
        "orig_pkts": 1,
        "resp_pkts": 2,
        "duration": 0.085,
        "local_orig": True,
        "local_resp": False,
        "query": "c2.stealth-botnet.org",
        "source": "zeek",
    }
    event = transform_to_flow_event(zeek_raw)
    assert isinstance(event, FlowEvent)
    assert event.flow_id == "CZeeK123456"
    assert event.src_ip == "10.0.0.15"
    assert event.dst_ip == "1.1.1.1"
    assert event.src_port == 49152
    assert event.dst_port == 53
    assert event.protocol == "UDP"
    assert event.bytes == 450
    assert event.packets == 3
    assert event.duration_ms == 85.0
    assert event.source == FlowSource.ZEEK
    assert event.dns is not None
    assert event.dns.query == "c2.stealth-botnet.org"


def test_normalize_suricata_record() -> None:
    """Test normalizing a native Suricata eve.json flow record."""
    suricata_raw = {
        "timestamp": "2026-08-26T12:10:00.000000+00:00",
        "event_type": "flow",
        "src_ip": "172.16.0.5",
        "src_port": 60000,
        "dest_ip": "172.16.0.10",
        "dest_port": 443,
        "proto": "TCP",
        "flow": {
            "id": 99887766,
            "pkts_toserver": 20,
            "pkts_toclient": 30,
            "bytes_toserver": 1500,
            "bytes_toclient": 4500,
            "age": 12.5,
        },
        "tls": {
            "sni": "internal-service.local",
            "ja3": "771,49195,0,23,0",
        },
        "source": "suricata",
    }
    event = transform_to_flow_event(suricata_raw)
    assert isinstance(event, FlowEvent)
    assert event.src_ip == "172.16.0.5"
    assert event.dst_ip == "172.16.0.10"
    assert event.protocol == "TCP"
    assert event.direction == FlowDirection.INTERNAL
    assert event.bytes == 6000
    assert event.packets == 50
    assert event.duration_ms == 12500.0
    assert event.source == FlowSource.SURICATA
    assert event.tls is not None
    assert event.tls.sni == "internal-service.local"


def test_normalize_netflow_record() -> None:
    """Test normalizing a decoded NetFlow/IPFIX JSON dictionary."""
    netflow_raw = {
        "srcaddr": "10.1.1.100",
        "dstaddr": "8.8.8.8",
        "srcport": 51234,
        "dstport": 53,
        "prot": 17,
        "protocol": "UDP",
        "dOctets": 512,
        "dPkts": 4,
        "duration": 50.0,
        "source": "netflow",
    }
    event = transform_to_flow_event(netflow_raw)
    assert isinstance(event, FlowEvent)
    assert event.src_ip == "10.1.1.100"
    assert event.dst_ip == "8.8.8.8"
    assert event.src_port == 51234
    assert event.dst_port == 53
    assert event.protocol == "UDP"
    assert event.bytes == 512
    assert event.packets == 4
    assert event.source == FlowSource.NETFLOW


# ==============================================================================
# Worker & Dead Letter Queue (DLQ) Tests
# ==============================================================================
def test_normalizer_worker_success() -> None:
    """Test normalizer worker successfully routing valid records to flow-events."""
    worker = FlowNormalizerWorker(
        bootstrap_servers="localhost:19092",
        dry_run=True,
    )

    valid_record = {
        "flow_id": "test-valid-1",
        "timestamp": "2026-08-26T12:00:00Z",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "src_port": 80,
        "dst_port": 8080,
        "protocol": "TCP",
        "bytes": 500,
        "packets": 5,
        "duration_ms": 10.0,
        "source": "pcap",
    }

    result = worker.process_record(valid_record)
    assert result is True
    assert worker.processed_count == 1
    assert worker.success_count == 1
    assert worker.dlq_count == 0


def test_normalizer_worker_routes_invalid_record_to_dlq() -> None:
    """Test corrupted record routing to DLQ without crashing."""
    worker = FlowNormalizerWorker(
        bootstrap_servers="localhost:19092",
        dry_run=True,
    )

    # Corrupt IP address
    corrupted_record = {
        "flow_id": "test-invalid-1",
        "src_ip": "999.999.999.999",  # Invalid IP
        "dst_ip": "10.0.0.2",
        "src_port": 80,
        "dst_port": 8080,
        "protocol": "TCP",
        "bytes": 500,
        "packets": 5,
        "source": "pcap",
    }

    result = worker.process_record(corrupted_record)
    assert result is False
    assert worker.processed_count == 1
    assert worker.success_count == 0
    assert worker.dlq_count == 1


def test_normalizer_worker_routes_malformed_json_to_dlq() -> None:
    """Test malformed string payload routing to DLQ."""
    worker = FlowNormalizerWorker(
        bootstrap_servers="localhost:19092",
        dry_run=True,
    )

    malformed_json = "{ invalid_json: true, no_quotes }"
    result = worker.process_record(malformed_json)
    assert result is False
    assert worker.dlq_count == 1
