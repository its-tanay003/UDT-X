"""Scenario 3: Volumetric SYN and UDP flood attack simulation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource


def generate_syn_udp_flood(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    target_ip: str = "10.0.0.50",
    count: int = 200,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface, target_ip=target_ip)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    for i in range(count):
        src_ip = f"192.168.1.{100 + (i % 80)}"
        proto = "TCP" if i % 4 != 0 else "UDP"
        dst_port = 80 if proto == "TCP" else 53

        ev = FlowEvent(
            timestamp=now,
            src_ip=src_ip,
            src_port=1024 + (i * 17) % 60000,
            dst_ip=target_ip,
            dst_port=dst_port,
            protocol=proto,
            direction=FlowDirection.INBOUND,
            source=FlowSource.NETFLOW,
            bytes=64 * 150,
            packets=150,
            duration_ms=10.0,
        )
        events.append(ev)

    ground_truth = {
        "scenario": "syn_udp_flood",
        "threat_class": "DDOS",
        "severity": "CRITICAL",
        "target_ip": target_ip,
        "event_count": len(events),
        "expected_alerts": 1,
        "mitre_technique": "T1498.001",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "syn_udp_flood_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "syn_udp_flood",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
