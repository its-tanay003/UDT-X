"""UDT-X Flow Normalizer Transformer Engine.

Polymorphically maps source-specific telemetry records (PCAP, NetFlow,
IPFIX, Zeek, Suricata) into validated canonical FlowEvent instances.
"""

import ipaddress
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from schema.models import (
    DNSData,
    FlowDirection,
    FlowEvent,
    FlowSource,
    TLSData,
)

logger = logging.getLogger("udtx.normalizer.transformer")


def determine_direction(src_ip_str: str, dst_ip_str: str) -> FlowDirection:
    """Classify traffic direction based on private vs public IP ranges."""
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


def normalize_timestamp(ts: Any) -> datetime:
    """Convert timestamp formats (epoch float, int, ISO string) to datetime."""
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=UTC)
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=UTC)
    if isinstance(ts, str) and ts.strip():
        # Handle trailing Z
        clean_ts = ts.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(clean_ts)
        except ValueError:
            # Fallback to float conversion if stringified epoch
            return datetime.fromtimestamp(float(clean_ts), tz=UTC)
    return datetime.now(UTC)


def transform_zeek_record(data: dict[str, Any]) -> FlowEvent:
    """Transform Zeek conn.log JSON format."""
    dt = normalize_timestamp(data.get("ts"))
    src_ip = data.get("id.orig_h") or data.get("src_ip")
    dst_ip = data.get("id.resp_h") or data.get("dst_ip")
    src_port = int(data.get("id.orig_p") or data.get("src_port") or 0)
    dst_port = int(data.get("id.resp_p") or data.get("dst_port") or 0)
    proto = str(data.get("proto") or "TCP").upper()

    orig_bytes = int(data.get("orig_bytes") or data.get("orig_ip_bytes") or 0)
    resp_bytes = int(data.get("resp_bytes") or data.get("resp_ip_bytes") or 0)
    orig_pkts = int(data.get("orig_pkts") or 1)
    resp_pkts = int(data.get("resp_pkts") or 0)
    duration_s = float(data.get("duration") or 0.0)

    dns_data = None
    if "query" in data:
        dns_data = DNSData(
            query=str(data["query"]),
            qtype=data.get("qtype_name") or data.get("qtype"),
        )

    tls_data = None
    if "ja3" in data or "server_name" in data or "sni" in data:
        tls_data = TLSData(
            ja3=data.get("ja3"),
            ja3s=data.get("ja3s"),
            sni=data.get("server_name") or data.get("sni"),
            cipher=data.get("cipher"),
        )

    return FlowEvent(
        flow_id=str(data.get("uid") or data.get("flow_id") or uuid.uuid4()),
        timestamp=dt,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=proto,
        direction=determine_direction(src_ip, dst_ip),
        bytes=orig_bytes + resp_bytes,
        packets=orig_pkts + resp_pkts,
        duration_ms=round(duration_s * 1000.0, 2),
        dns=dns_data,
        tls=tls_data,
        source=FlowSource.ZEEK,
        schema_version="1.0.0",
    )


def transform_suricata_record(data: dict[str, Any]) -> FlowEvent:
    """Transform Suricata eve.json flow format."""
    dt = normalize_timestamp(data.get("timestamp"))
    flow_info = data.get("flow", {})

    src_ip = data.get("src_ip") or data.get("src")
    dst_ip = data.get("dest_ip") or data.get("dst_ip") or data.get("dest")
    src_port = int(data.get("src_port") or data.get("sport") or 0)
    dst_port = int(
        data.get("dest_port") or data.get("dst_port") or data.get("dport") or 0
    )
    proto = str(data.get("proto") or "TCP").upper()

    bytes_toserver = int(
        flow_info.get("bytes_toserver") or data.get("bytes_toserver") or 0
    )
    bytes_toclient = int(
        flow_info.get("bytes_toclient") or data.get("bytes_toclient") or 0
    )
    pkts_toserver = int(
        flow_info.get("pkts_toserver") or data.get("pkts_toserver") or 1
    )
    pkts_toclient = int(
        flow_info.get("pkts_toclient") or data.get("pkts_toclient") or 0
    )
    age = float(flow_info.get("age") or data.get("duration") or 0.0)

    dns_data = None
    if "dns" in data:
        d = data["dns"]
        dns_data = DNSData(
            query=str(d.get("rrname") or d.get("query") or ""),
            qtype=d.get("rrtype") or d.get("qtype"),
        )

    tls_data = None
    if "tls" in data:
        t = data["tls"]
        tls_data = TLSData(
            sni=t.get("sni"),
            ja3=t.get("ja3", {}).get("hash")
            if isinstance(t.get("ja3"), dict)
            else t.get("ja3"),
            ja3s=t.get("ja3s", {}).get("hash")
            if isinstance(t.get("ja3s"), dict)
            else t.get("ja3s"),
            cipher=t.get("version"),
        )

    return FlowEvent(
        flow_id=str(flow_info.get("id") or data.get("flow_id") or uuid.uuid4()),
        timestamp=dt,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=proto,
        direction=determine_direction(src_ip, dst_ip),
        bytes=bytes_toserver + bytes_toclient,
        packets=pkts_toserver + pkts_toclient,
        duration_ms=round(age * 1000.0, 2),
        dns=dns_data,
        tls=tls_data,
        source=FlowSource.SURICATA,
        schema_version="1.0.0",
    )


def transform_netflow_record(data: dict[str, Any]) -> FlowEvent:
    """Transform NetFlow / IPFIX JSON representation."""
    dt = normalize_timestamp(data.get("timestamp") or data.get("time"))
    src_ip = data.get("src_ip") or data.get("srcaddr") or data.get("src")
    dst_ip = (
        data.get("dst_ip")
        or data.get("dstaddr")
        or data.get("dest_ip")
        or data.get("dst")
    )
    src_port = int(data.get("src_port") or data.get("srcport") or 0)
    dst_port = int(
        data.get("dst_port") or data.get("dstport") or data.get("dest_port") or 0
    )
    proto = str(data.get("protocol") or data.get("prot") or "TCP").upper()

    total_bytes = int(
        data.get("bytes") or data.get("dOctets") or data.get("octets") or 0
    )
    total_packets = int(
        data.get("packets") or data.get("dPkts") or data.get("pkts") or 1
    )
    duration_ms = float(data.get("duration_ms") or data.get("duration") or 0.0)

    source_val = str(data.get("source") or "netflow").lower()
    source_enum = FlowSource.IPFIX if "ipfix" in source_val else FlowSource.NETFLOW

    return FlowEvent(
        flow_id=str(data.get("flow_id") or uuid.uuid4()),
        timestamp=dt,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=proto,
        direction=determine_direction(src_ip, dst_ip),
        bytes=total_bytes,
        packets=total_packets,
        duration_ms=duration_ms,
        source=source_enum,
        schema_version="1.0.0",
    )


def transform_to_flow_event(raw_data: Any) -> FlowEvent:
    """Polymorphically detect format and transform into validated FlowEvent.

    Raises ValueError or pydantic.ValidationError if record is invalid.
    """
    if not isinstance(raw_data, dict):
        raise ValueError(f"Expected JSON object / dict, got {type(raw_data).__name__}")

    # 1. Direct Canonical FlowEvent dictionary
    if "flow_id" in raw_data and "source" in raw_data and "bytes" in raw_data:
        try:
            return FlowEvent.model_validate(raw_data)
        except Exception:
            pass  # Attempt specialized mapping if validation fails

    # 2. Zeek conn.log pattern
    if "id.orig_h" in raw_data or raw_data.get("source") == "zeek":
        return transform_zeek_record(raw_data)

    # 3. Suricata EVE pattern
    if "event_type" in raw_data or raw_data.get("source") == "suricata":
        return transform_suricata_record(raw_data)

    # 4. NetFlow / IPFIX pattern
    if (
        "dOctets" in raw_data
        or "srcaddr" in raw_data
        or str(raw_data.get("source")).lower() in ("netflow", "ipfix")
    ):
        return transform_netflow_record(raw_data)

    # 5. Generic dictionary fallback
    src_ip = raw_data.get("src_ip") or raw_data.get("source_ip") or raw_data.get("src")
    dst_ip = (
        raw_data.get("dst_ip")
        or raw_data.get("destination_ip")
        or raw_data.get("dest_ip")
        or raw_data.get("dst")
    )
    src_port = int(
        raw_data.get("src_port")
        or raw_data.get("source_port")
        or raw_data.get("sport")
        or 0
    )
    dst_port = int(
        raw_data.get("dst_port")
        or raw_data.get("destination_port")
        or raw_data.get("dport")
        or 0
    )
    proto = str(raw_data.get("protocol") or raw_data.get("proto") or "TCP")

    total_bytes = int(
        raw_data.get("bytes")
        or raw_data.get("total_bytes")
        or raw_data.get("byte_count")
        or 0
    )
    total_packets = int(
        raw_data.get("packets")
        or raw_data.get("total_packets")
        or raw_data.get("packet_count")
        or 0
    )
    duration_ms = float(raw_data.get("duration_ms") or raw_data.get("duration") or 0.0)
    source_val = str(raw_data.get("source") or "pcap").lower()

    valid_sources = {
        "pcap": FlowSource.PCAP,
        "netflow": FlowSource.NETFLOW,
        "ipfix": FlowSource.IPFIX,
        "sflow": FlowSource.SFLOW,
        "zeek": FlowSource.ZEEK,
        "suricata": FlowSource.SURICATA,
    }
    source_enum = valid_sources.get(source_val, FlowSource.PCAP)

    dt = normalize_timestamp(raw_data.get("timestamp") or raw_data.get("time"))

    return FlowEvent(
        flow_id=str(raw_data.get("flow_id") or uuid.uuid4()),
        timestamp=dt,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=proto,
        direction=determine_direction(src_ip, dst_ip),
        bytes=total_bytes,
        packets=total_packets,
        duration_ms=duration_ms,
        source=source_enum,
        schema_version="1.0.0",
    )
