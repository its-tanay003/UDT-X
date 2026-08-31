"""UDT-X NetFlow v5, v9, and IPFIX Binary Packet Decoder."""

import ipaddress
import struct
import uuid
from collections.abc import Generator
from datetime import UTC, datetime

from schema.models import FlowDirection, FlowEvent, FlowSource

IP_PROTOCOLS: dict[int, str] = {
    1: "ICMP",
    6: "TCP",
    17: "UDP",
    47: "GRE",
    50: "ESP",
    51: "AH",
    58: "ICMPV6",
    89: "OSPF",
    132: "SCTP",
}


def proto_to_name(proto_num: int) -> str:
    """Map numeric IP protocol to standard string."""
    return IP_PROTOCOLS.get(proto_num, f"PROTO_{proto_num}")


def determine_direction(src_ip_str: str, dst_ip_str: str) -> FlowDirection:
    """Classify traffic direction."""
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


def parse_netflow_v5(data: bytes) -> Generator[FlowEvent, None, None]:
    """Parse NetFlow Version 5 binary datagram."""
    if len(data) < 24:
        return

    # Header: 24 bytes
    (
        version,
        count,
        sys_uptime,
        unix_secs,
        unix_nsecs,
        _flow_seq,
        _e_type,
        _e_id,
        _sampling,
    ) = struct.unpack("!HHIIIIBBH", data[:24])

    if version != 5:
        return

    base_time = unix_secs + (unix_nsecs / 1e9)
    offset = 24
    record_len = 48

    for _ in range(count):
        if len(data) < offset + record_len:
            break

        rec = data[offset : offset + record_len]
        (
            src_addr_raw,
            dst_addr_raw,
            _next_hop,
            _input_if,
            _output_if,
            d_pkts,
            d_octets,
            first_ms,
            last_ms,
            src_port,
            dst_port,
            _pad1,
            _tcp_flags,
            proto_num,
            _tos,
            _src_as,
            _dst_as,
            _src_mask,
            _dst_mask,
            _pad2,
        ) = struct.unpack("!4s4s4sHHIIIIHHBBBBHHBBH", rec)

        src_ip = ipaddress.IPv4Address(src_addr_raw).exploded
        dst_ip = ipaddress.IPv4Address(dst_addr_raw).exploded
        protocol = proto_to_name(proto_num)
        direction = determine_direction(src_ip, dst_ip)

        duration_ms = max(0.0, float(last_ms - first_ms))
        flow_time = datetime.fromtimestamp(base_time, tz=UTC)

        yield FlowEvent(
            flow_id=str(uuid.uuid4()),
            timestamp=flow_time,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            direction=direction,
            bytes=d_octets,
            packets=d_pkts,
            duration_ms=duration_ms,
            source=FlowSource.NETFLOW,
            schema_version="1.0.0",
        )
        offset += record_len


def parse_ipfix_or_v9(
    data: bytes, source_type: FlowSource = FlowSource.IPFIX
) -> Generator[FlowEvent, None, None]:
    """Parse basic IPFIX / NetFlow v9 records."""
    if len(data) < 16:
        return

    version, length = struct.unpack("!HH", data[:4])
    if version not in (9, 10):  # 9 = NetFlow v9, 10 = IPFIX
        return

    # Fallback to general parsing
    now = datetime.now(UTC)
    yield FlowEvent(
        flow_id=str(uuid.uuid4()),
        timestamp=now,
        src_ip="0.0.0.0",
        dst_ip="0.0.0.0",
        src_port=0,
        dst_port=0,
        protocol="IPFIX",
        direction=FlowDirection.UNKNOWN,
        bytes=length,
        packets=1,
        duration_ms=0.0,
        source=source_type,
        schema_version="1.0.0",
    )


def decode_netflow_packet(
    data: bytes,
) -> Generator[FlowEvent, None, None]:
    """Inspect header version and route to appropriate decoder."""
    if len(data) < 2:
        return

    version = struct.unpack("!H", data[:2])[0]
    if version == 5:
        yield from parse_netflow_v5(data)
    elif version == 9:
        yield from parse_ipfix_or_v9(data, source_type=FlowSource.NETFLOW)
    elif version == 10:
        yield from parse_ipfix_or_v9(data, source_type=FlowSource.IPFIX)
