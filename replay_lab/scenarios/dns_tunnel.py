"""Scenario 7: DNS Tunneling data exfiltration emulator."""

from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import DNSData, FlowDirection, FlowEvent, FlowSource


def generate_dns_tunnel(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    client_ip: str = "192.168.1.130",
    dns_server_ip: str = "8.8.8.8",
    base_domain: str = "tunnel.exfil-lab.org",
    chunks_count: int = 30,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface, target_ip=client_ip)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    for i in range(chunks_count):
        raw_payload = os.urandom(16)
        encoded_sub = (
            base64.b32encode(raw_payload)
            .decode("utf-8")
            .lower()
            .replace("=", "")
        )
        full_query = f"{encoded_sub}.{i}.{base_domain}"

        ev = FlowEvent(
            timestamp=now,
            src_ip=client_ip,
            src_port=53000 + i,
            dst_ip=dns_server_ip,
            dst_port=53,
            protocol="UDP",
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=290,
            packets=2,
            duration_ms=35.0,
            dns=DNSData(query=full_query),
        )
        events.append(ev)

    ground_truth = {
        "scenario": "dns_tunnel",
        "threat_class": "DNS_TUNNELING",
        "severity": "CRITICAL",
        "client_ip": client_ip,
        "base_domain": base_domain,
        "tunnel_chunks": len(events),
        "expected_alerts": 1,
        "mitre_technique": "T1071.004",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "dns_tunnel_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "dns_tunnel",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
