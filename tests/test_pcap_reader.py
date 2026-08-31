"""Smoke and unit tests for PCAP Ingestion Reader."""

import tempfile
from pathlib import Path

from scapy.all import DNS, DNSQR, IP, TCP, UDP, Raw, wrpcap

from ingestion.kafka_producer import UDTXKafkaProducer
from ingestion.pcap_reader.pcap_extractor import extract_flows_from_pcap
from schema.models import FlowDirection, FlowEvent, FlowSource


def create_synthetic_pcap(output_path: Path) -> None:
    """Generate a realistic synthetic PCAP file with TCP and DNS flows."""
    packets = []

    # 1. TCP Web Traffic Flow: 192.168.1.100:45678 -> 93.184.216.34:80 (example.com)
    syn = IP(src="192.168.1.100", dst="93.184.216.34") / TCP(
        sport=45678, dport=80, flags="S", seq=1000
    )
    syn.time = 1724670000.0
    packets.append(syn)

    syn_ack = IP(src="93.184.216.34", dst="192.168.1.100") / TCP(
        sport=80, dport=45678, flags="SA", seq=2000, ack=1001
    )
    syn_ack.time = 1724670000.02
    packets.append(syn_ack)

    http_get = (
        IP(src="192.168.1.100", dst="93.184.216.34")
        / TCP(sport=45678, dport=80, flags="PA", seq=1001, ack=2001)
        / Raw(load=b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n")
    )
    http_get.time = 1724670000.05
    packets.append(http_get)

    # 2. UDP DNS Query Flow: 192.168.1.100:53535 -> 8.8.8.8:53
    dns_query = (
        IP(src="192.168.1.100", dst="8.8.8.8")
        / UDP(sport=53535, dport=53)
        / DNS(rd=1, qd=DNSQR(qname="malicious-c2-beacon.corp.internal", qtype="A"))
    )
    dns_query.time = 1724670001.10
    packets.append(dns_query)

    wrpcap(str(output_path), packets)


def test_pcap_flow_extraction() -> None:
    """Verify flow extraction accuracy from synthetic PCAP."""
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        create_synthetic_pcap(tmp_path)
        flows = list(extract_flows_from_pcap(tmp_path))

        assert len(flows) >= 2, f"Expected at least 2 flows, got {len(flows)}"

        # Check for DNS flow
        dns_flows = [f for f in flows if f.protocol == "UDP" and f.dst_port == 53]
        assert len(dns_flows) == 1
        dns_flow = dns_flows[0]
        assert dns_flow.src_ip == "192.168.1.100"
        assert dns_flow.dst_ip == "8.8.8.8"
        assert dns_flow.source == FlowSource.PCAP
        assert dns_flow.dns is not None
        assert dns_flow.dns.query == "malicious-c2-beacon.corp.internal"
        assert dns_flow.dns.entropy is not None
        assert dns_flow.dns.entropy > 2.0

        # Check for TCP flow
        tcp_flows = [f for f in flows if f.protocol == "TCP"]
        assert len(tcp_flows) >= 1
        tcp_out = [f for f in tcp_flows if f.dst_port == 80][0]
        assert tcp_out.src_ip == "192.168.1.100"
        assert tcp_out.dst_ip == "93.184.216.34"
        assert tcp_out.packets == 2
        assert tcp_out.bytes > 100
        assert tcp_out.direction == FlowDirection.OUTBOUND
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_pcap_kafka_publisher_smoke() -> None:
    """Verify that FlowEvents can be sent to Kafka producer."""
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        create_synthetic_pcap(tmp_path)
        producer = UDTXKafkaProducer(
            bootstrap_servers="localhost:19092",
            topic="raw-events",
            dry_run=True,  # Test dry-run buffer / serialization path
        )

        count = 0
        for flow in extract_flows_from_pcap(tmp_path):
            assert isinstance(flow, FlowEvent)
            event_dict = flow.model_dump(mode="json")
            res = producer.send_event(event_dict, key=flow.flow_id)
            assert res is True
            count += 1

        producer.flush()
        producer.close()
        assert count >= 2
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
