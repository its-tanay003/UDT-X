"""UDT-X Suricata EVE JSON Log Adapter.

Normalizes Suricata eve.json flow and alert events into canonical UDT-X records.
"""

import json
import logging
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

logger = logging.getLogger("udtx.suricata_adapter")

SURICATA_SEVERITY_MAP: dict[int, SeverityLevel] = {
    1: SeverityLevel.HIGH,
    2: SeverityLevel.MEDIUM,
    3: SeverityLevel.LOW,
    4: SeverityLevel.INFO,
}


def parse_suricata_flow_record(rec: dict[str, Any]) -> FlowEvent | None:
    """Transform Suricata eve.json 'flow' or 'netflow' event into FlowEvent."""
    try:
        ts_str = rec.get("timestamp")
        dt = (
            datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts_str
            else datetime.now(UTC)
        )

        flow_info = rec.get("flow", {})
        proto = str(rec.get("proto") or "TCP").upper()

        src_ip = rec.get("src_ip", "0.0.0.0")
        dst_ip = rec.get("dest_ip") or rec.get("dst_ip", "0.0.0.0")
        src_port = int(rec.get("src_port", 0))
        dst_port = int(rec.get("dest_port") or rec.get("dst_port", 0))

        bytes_toserver = int(flow_info.get("bytes_toserver", 0))
        bytes_toclient = int(flow_info.get("bytes_toclient", 0))
        pkts_toserver = int(flow_info.get("pkts_toserver", 1))
        pkts_toclient = int(flow_info.get("pkts_toclient", 0))
        age = float(flow_info.get("age", 0.0))

        # Check for nested DNS or TLS
        dns_data = None
        if "dns" in rec:
            dns_info = rec["dns"]
            dns_data = DNSData(
                query=str(dns_info.get("rrname") or dns_info.get("query", "")),
                qtype=dns_info.get("rrtype") or dns_info.get("qtype"),
            )

        tls_data = None
        if "tls" in rec:
            tls_info = rec["tls"]
            tls_data = TLSData(
                sni=tls_info.get("sni"),
                ja3=tls_info.get("ja3", {}).get("hash")
                if isinstance(tls_info.get("ja3"), dict)
                else tls_info.get("ja3"),
                ja3s=tls_info.get("ja3s", {}).get("hash")
                if isinstance(tls_info.get("ja3s"), dict)
                else tls_info.get("ja3s"),
                cipher=tls_info.get("version"),
            )

        return FlowEvent(
            flow_id=str(flow_info.get("id") or rec.get("flow_id") or uuid.uuid4()),
            timestamp=dt,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=proto,
            direction=FlowDirection.UNKNOWN,
            bytes=bytes_toserver + bytes_toclient,
            packets=pkts_toserver + pkts_toclient,
            duration_ms=round(age * 1000.0, 2),
            dns=dns_data,
            tls=tls_data,
            source=FlowSource.SURICATA,
            schema_version="1.0.0",
        )
    except Exception as exc:
        logger.warning("Failed to parse Suricata flow record: %s (%s)", rec, exc)
        return None


def parse_suricata_alert_record(rec: dict[str, Any]) -> Alert | None:
    """Transform Suricata eve.json 'alert' event into canonical Alert."""
    try:
        alert_info = rec.get("alert", {})
        ts_str = rec.get("timestamp")
        dt = (
            datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts_str
            else datetime.now(UTC)
        )

        severity_num = int(alert_info.get("severity", 3))
        severity = SURICATA_SEVERITY_MAP.get(severity_num, SeverityLevel.MEDIUM)

        evidence = [
            EvidenceItem(
                key="signature_id",
                value=alert_info.get("signature_id"),
                description=alert_info.get("signature", "Suricata Alert"),
            ),
            EvidenceItem(
                key="category",
                value=alert_info.get("category", "Generic"),
                description="Suricata attack classification category",
            ),
        ]

        # Extract MITRE metadata if embedded in metadata
        mitre_list: list[MitreAttack] = []
        meta = alert_info.get("metadata", {})
        if "mitre_technique_id" in meta:
            for t_id in meta["mitre_technique_id"]:
                mitre_list.append(
                    MitreAttack(
                        technique_id=t_id,
                        technique_name=alert_info.get("signature", "Signature"),
                    )
                )

        return Alert(
            alert_id=str(rec.get("flow_id") or uuid.uuid4()),
            timestamp=dt,
            flow_id=str(rec.get("flow_id")) if rec.get("flow_id") else None,
            src_ip=rec.get("src_ip", "0.0.0.0"),
            dst_ip=rec.get("dest_ip") or rec.get("dst_ip", "0.0.0.0"),
            protocol=str(rec.get("proto") or "TCP").upper(),
            threat_class=alert_info.get("category", "intrusion_detection"),
            severity=severity,
            confidence=0.85,
            risk_score=75.0 if severity == SeverityLevel.HIGH else 45.0,
            evidence=evidence,
            mitre=mitre_list,
            title=alert_info.get("signature", "Suricata Signature Alert"),
            description=f"Suricata alert category: {alert_info.get('category')}",
            status=AlertStatus.OPEN,
            schema_version="1.0.0",
        )
    except Exception as exc:
        logger.warning("Failed to parse Suricata alert record: %s (%s)", rec, exc)
        return None


def stream_suricata_eve_file(
    file_path: Path,
) -> Generator[FlowEvent | Alert, None, None]:
    """Read a Suricata eve.json log and yield normalized FlowEvents or Alerts."""
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ev_type = rec.get("event_type")
                if ev_type in ("flow", "netflow", "dns", "tls"):
                    event = parse_suricata_flow_record(rec)
                    if event:
                        yield event
                elif ev_type == "alert":
                    alert = parse_suricata_alert_record(rec)
                    if alert:
                        yield alert
            except json.JSONDecodeError:
                continue
