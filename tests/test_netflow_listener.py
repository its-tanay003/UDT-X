"""Unit tests for NetFlow v5/v9 and IPFIX decoder."""

import ipaddress
import struct

from ingestion.netflow_listener.parser import decode_netflow_packet
from schema.models import FlowDirection, FlowSource


def build_synthetic_netflow_v5_packet() -> bytes:
    """Construct a valid 72-byte NetFlow v5 packet."""
    # Header: version=5, count=1, sys_uptime=100000, unix_secs=1724670000
    header = struct.pack(
        "!HHIIIIBBH",
        5,  # version
        1,  # count
        100000,  # sys_uptime
        1724670000,  # unix_secs
        0,  # unix_nsecs
        1,  # flow_sequence
        0,  # engine_type
        0,  # engine_id
        0,  # sampling_interval
    )

    src_bytes = ipaddress.IPv4Address("10.0.1.5").packed
    dst_bytes = ipaddress.IPv4Address("93.184.216.34").packed
    nexthop_bytes = ipaddress.IPv4Address("10.0.1.1").packed

    # Record: 48 bytes
    record = struct.pack(
        "!4s4s4sHHIIIIHHBBBBHHBBH",
        src_bytes,  # srcaddr
        dst_bytes,  # dstaddr
        nexthop_bytes,  # nexthop
        1,  # input ifindex
        2,  # output ifindex
        15,  # dPkts
        1500,  # dOctets
        1000,  # First ms
        5000,  # Last ms
        54321,  # srcport
        443,  # dstport
        0,  # pad1
        0x18,  # tcp_flags (PSH+ACK)
        6,  # prot (TCP = 6)
        0,  # tos
        65001,  # src_as
        65002,  # dst_as
        24,  # src_mask
        32,  # dst_mask
        0,  # pad2
    )

    return header + record


def test_decode_netflow_v5() -> None:
    """Verify decoding a binary NetFlow v5 packet into canonical FlowEvent."""
    packet = build_synthetic_netflow_v5_packet()
    flows = list(decode_netflow_packet(packet))

    assert len(flows) == 1
    flow = flows[0]
    assert flow.src_ip == "10.0.1.5"
    assert flow.dst_ip == "93.184.216.34"
    assert flow.src_port == 54321
    assert flow.dst_port == 443
    assert flow.protocol == "TCP"
    assert flow.packets == 15
    assert flow.bytes == 1500
    assert flow.duration_ms == 4000.0
    assert flow.direction == FlowDirection.OUTBOUND
    assert flow.source == FlowSource.NETFLOW
