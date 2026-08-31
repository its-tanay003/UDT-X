"""UDT-X Zeek Log Adapter.

Normalizes Zeek conn.log, dns.log, and ssl.log JSON records into FlowEvents.
"""

import json
import logging
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from schema.models import (
    DNSData,
    FlowDirection,
    FlowEvent,
    FlowSource,
    TLSData,
)

logger = logging.getLogger("udtx.zeek_adapter")


def parse_zeek_conn_record(record: dict[str, Any]) -> FlowEvent | None:
    """Transform a Zeek conn.log JSON record into a canonical FlowEvent."""
    try:
        ts = record.get("ts")
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=UTC)
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.now(UTC)

        src_ip = record.get("id.orig_h") or record.get("src_ip", "0.0.0.0")
        dst_ip = record.get("id.resp_h") or record.get("dst_ip", "0.0.0.0")
        src_port = int(record.get("id.orig_p") or record.get("src_port", 0))
        dst_port = int(record.get("id.resp_p") or record.get("dst_port", 0))
        proto = str(record.get("proto") or "TCP").upper()

        orig_bytes = int(record.get("orig_bytes") or record.get("orig_ip_bytes") or 0)
        resp_bytes = int(record.get("resp_bytes") or record.get("resp_ip_bytes") or 0)
        orig_pkts = int(record.get("orig_pkts") or 1)
        resp_pkts = int(record.get("resp_pkts") or 0)
        duration_s = float(record.get("duration") or 0.0)

        # Direction detection
        local_orig = record.get("local_orig", False)
        local_resp = record.get("local_resp", False)
        if local_orig and not local_resp:
            direction = FlowDirection.OUTBOUND
        elif not local_orig and local_resp:
            direction = FlowDirection.INBOUND
        elif local_orig and local_resp:
            direction = FlowDirection.INTERNAL
        else:
            direction = FlowDirection.EXTERNAL

        # Optional DNS / SSL info if augmented in record
        dns_data = None
        if "query" in record:
            dns_data = DNSData(
                query=str(record["query"]),
                qtype=record.get("qtype_name"),
            )

        tls_data = None
        if "ja3" in record or "server_name" in record:
            tls_data = TLSData(
                ja3=record.get("ja3"),
                ja3s=record.get("ja3s"),
                sni=record.get("server_name"),
                cipher=record.get("cipher"),
            )

        return FlowEvent(
            flow_id=str(record.get("uid") or uuid.uuid4()),
            timestamp=dt,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=proto,
            direction=direction,
            bytes=orig_bytes + resp_bytes,
            packets=orig_pkts + resp_pkts,
            duration_ms=round(duration_s * 1000.0, 2),
            dns=dns_data,
            tls=tls_data,
            source=FlowSource.ZEEK,
            schema_version="1.0.0",
        )
    except Exception as exc:
        logger.warning("Failed to parse Zeek record: %s (%s)", record, exc)
        return None


def stream_zeek_log_file(file_path: Path) -> Generator[FlowEvent, None, None]:
    """Read a Zeek JSON log file line by line and yield FlowEvents."""
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rec = json.loads(line)
                event = parse_zeek_conn_record(rec)
                if event:
                    yield event
            except json.JSONDecodeError:
                continue
