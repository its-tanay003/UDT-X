"""UDT-X PCAP Flow Extractor Engine."""

import ipaddress
import math
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from schema.models import (
    DNSData,
    FlowDirection,
    FlowEvent,
    FlowSource,
    TLSData,
)


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy for a string (used for DNS DGA detection)."""
    if not text:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return -sum(p * math.log2(p) for p in prob if p > 0)


def determine_direction(src_ip_str: str, dst_ip_str: str) -> FlowDirection:
    """Determine traffic direction based on RFC 1918 private IP."""
    try:
        src = ipaddress.ip_address(src_ip_str)
        dst = ipaddress.ip_address(dst_ip_str)

        if src.is_private and dst.is_private:
            return FlowDirection.INTERNAL
        if src.is_private and not dst.is_private:
            return FlowDirection.OUTBOUND
        if not src.is_private and dst.is_private:
            return FlowDirection.INBOUND
        return FlowDirection.EXTERNAL
    except Exception:
        return FlowDirection.UNKNOWN


class FlowAccumulator:
    """Tracks state and metrics for a unidirectional or bidirectional flow."""

    def __init__(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        start_time: float,
    ) -> None:
        self.flow_id = str(uuid.uuid4())
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol.upper()
        self.start_time = start_time
        self.end_time = start_time
        self.total_bytes = 0
        self.total_packets = 0
        self.packet_sizes: list[int] = []
        self.dns_data: DNSData | None = None
        self.tls_data: TLSData | None = None

    def add_packet(
        self,
        pkt_len: int,
        timestamp: float,
        dns_query: str | None = None,
        dns_qtype: str | int | None = None,
        tls_sni: str | None = None,
        ja3_hash: str | None = None,
    ) -> None:
        self.total_bytes += pkt_len
        self.total_packets += 1
        self.end_time = max(self.end_time, timestamp)
        if len(self.packet_sizes) < 32:
            self.packet_sizes.append(pkt_len)

        if dns_query and self.dns_data is None:
            self.dns_data = DNSData(
                query=dns_query,
                qtype=dns_qtype,
                entropy=round(calculate_entropy(dns_query), 4),
            )

        if (tls_sni or ja3_hash) and self.tls_data is None:
            self.tls_data = TLSData(
                sni=tls_sni,
                ja3=ja3_hash,
                packet_size_sequence=self.packet_sizes,
            )
        elif self.tls_data is not None:
            self.tls_data.packet_size_sequence = self.packet_sizes

    def to_flow_event(self) -> FlowEvent:
        duration_ms = max(0.0, (self.end_time - self.start_time) * 1000.0)
        dt = datetime.fromtimestamp(self.start_time, tz=UTC)
        direction = determine_direction(self.src_ip, self.dst_ip)

        return FlowEvent(
            flow_id=self.flow_id,
            timestamp=dt,
            src_ip=self.src_ip,
            dst_ip=self.dst_ip,
            src_port=self.src_port,
            dst_port=self.dst_port,
            protocol=self.protocol,
            direction=direction,
            bytes=self.total_bytes,
            packets=self.total_packets,
            duration_ms=round(duration_ms, 2),
            dns=self.dns_data,
            tls=self.tls_data,
            source=FlowSource.PCAP,
            schema_version="1.0.0",
        )


def extract_flows_from_pcap(
    pcap_path: str | Path,
) -> Generator[FlowEvent, None, None]:
    """Read a .pcap/.pcapng file using Scapy or Dpkt and yield FlowEvents."""
    pcap_file = Path(pcap_path)
    if not pcap_file.exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_file}")

    from scapy.all import DNS, DNSQR, IP, TCP, UDP, IPv6, PcapReader

    flows: dict[tuple[str, str, int, int, str], FlowAccumulator] = {}

    with PcapReader(str(pcap_file)) as reader:
        for pkt in reader:
            if not (pkt.haslayer(IP) or pkt.haslayer(IPv6)):
                continue

            # Extract IP layer
            if pkt.haslayer(IP):
                ip_layer = pkt[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
            else:
                ip_layer = pkt[IPv6]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst

            # Extract Transport layer
            if pkt.haslayer(TCP):
                tcp_layer = pkt[TCP]
                src_port = int(tcp_layer.sport)
                dst_port = int(tcp_layer.dport)
                protocol = "TCP"
            elif pkt.haslayer(UDP):
                udp_layer = pkt[UDP]
                src_port = int(udp_layer.sport)
                dst_port = int(udp_layer.dport)
                protocol = "UDP"
            else:
                src_port = 0
                dst_port = 0
                proto_num = ip_layer.proto if hasattr(ip_layer, "proto") else 0
                protocol = f"PROTO_{proto_num}"

            flow_key = (src_ip, dst_ip, src_port, dst_port, protocol)
            timestamp = float(pkt.time)
            pkt_len = len(pkt)

            # Deep Packet Inspection (DNS / TLS)
            dns_query = None
            dns_qtype = None
            if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
                try:
                    qname = pkt[DNSQR].qname
                    if isinstance(qname, bytes):
                        dns_query = qname.decode("utf-8", errors="ignore").rstrip(".")
                    else:
                        dns_query = str(qname).rstrip(".")
                    dns_qtype = str(pkt[DNSQR].qtype)
                except Exception:
                    pass

            tls_sni = None
            if (dst_port == 443 or src_port == 443) and pkt.haslayer(TCP):
                raw_payload = bytes(pkt[TCP].payload)
                if len(raw_payload) > 5 and raw_payload[0] == 0x16:
                    try:
                        idx = raw_payload.find(b"\x00\x00")
                        if idx != -1 and idx + 5 < len(raw_payload):
                            tls_sni = None
                    except Exception:
                        pass

            if flow_key not in flows:
                flows[flow_key] = FlowAccumulator(
                    src_ip, dst_ip, src_port, dst_port, protocol, timestamp
                )

            flows[flow_key].add_packet(
                pkt_len=pkt_len,
                timestamp=timestamp,
                dns_query=dns_query,
                dns_qtype=dns_qtype,
                tls_sni=tls_sni,
            )

    for flow in flows.values():
        yield flow.to_flow_event()
