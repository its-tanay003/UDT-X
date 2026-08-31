"""Scenario 2: High-Volume legitimate burst traffic."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource


def generate_high_volume_legitimate(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    count: int = 150,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    for i in range(count):
        src_ip = f"192.168.1.{10 + (i % 30)}"
        dst_ip = "10.0.0.100"
        ev = FlowEvent(
            timestamp=now,
            src_ip=src_ip,
            src_port=30000 + i,
            dst_ip=dst_ip,
            dst_port=443,
            protocol="TCP",
            direction=FlowDirection.INTERNAL,
            source=FlowSource.PCAP,
            bytes=57000 + (i * 300),
            packets=130,
            duration_ms=1200.0,
        )
        events.append(ev)

    ground_truth = {
        "scenario": "high_volume_legitimate",
        "label": "BENIGN_BURST",
        "expected_alerts": 0,
        "event_count": len(events),
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "high_volume_legitimate_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "high_volume_legitimate",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
