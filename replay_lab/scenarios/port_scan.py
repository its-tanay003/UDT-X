"""Scenario 4: Horizontal & Vertical Port Scan reconnaissance scenario."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource


def generate_port_scan(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    scanner_ip: str = "192.168.1.105",
    target_ip: str = "10.0.0.1",
    ports_to_probe: list[int] | None = None,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface, target_ip=scanner_ip)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if ports_to_probe is None:
        ports_to_probe = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
            1723, 3306, 3389, 5900, 8080, 8443, 8888, 9000, 9092, 27017,
        ]

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    for port in ports_to_probe:
        ev = FlowEvent(
            timestamp=now,
            src_ip=scanner_ip,
            src_port=54000 + (port % 1000),
            dst_ip=target_ip,
            dst_port=port,
            protocol="TCP",
            direction=FlowDirection.INTERNAL,
            source=FlowSource.ZEEK,
            bytes=44,
            packets=1,
            duration_ms=1.0,
        )
        events.append(ev)

    ground_truth = {
        "scenario": "port_scan",
        "threat_class": "RECONNAISSANCE",
        "severity": "MEDIUM",
        "scanner_ip": scanner_ip,
        "target_ip": target_ip,
        "ports_probed_count": len(ports_to_probe),
        "expected_alerts": 1,
        "mitre_technique": "T1046",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "port_scan_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "port_scan",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
