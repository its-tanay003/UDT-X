"""Scenario 5: Periodic Command & Control (C2) beacon emulator."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource, TLSData


def generate_c2_beacon(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    infected_host_ip: str = "192.168.1.105",
    c2_server_ip: str = "198.51.100.22",
    beacon_interval_sec: float = 10.0,
    jitter_pct: float = 0.05,
    beacon_count: int = 25,
) -> dict[str, Any]:
    validate_lab_environment(
        target_interface=target_interface, target_ip=infected_host_ip
    )
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now(UTC)
    events: list[FlowEvent] = []

    for i in range(beacon_count):
        delta = (i * beacon_interval_sec) + random.uniform(
            -beacon_interval_sec * jitter_pct, beacon_interval_sec * jitter_pct
        )
        beacon_time = start_time + timedelta(seconds=max(0, delta))

        ev = FlowEvent(
            timestamp=beacon_time,
            src_ip=infected_host_ip,
            src_port=49500 + i,
            dst_ip=c2_server_ip,
            dst_port=443,
            protocol="TCP",
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=640,
            packets=10,
            duration_ms=120.0,
            tls=TLSData(
                ja3="e7d705a3286e19ea42f587b344ee6865",
                sni="update-check.services-sync.net",
            ),
        )
        events.append(ev)

    ground_truth = {
        "scenario": "c2_beacon",
        "threat_class": "C2_BEACONING",
        "severity": "HIGH",
        "infected_host_ip": infected_host_ip,
        "c2_server_ip": c2_server_ip,
        "beacon_count": len(events),
        "expected_alerts": 1,
        "mitre_technique": "T1071.004",
        "created_at": start_time.isoformat(),
    }

    gt_file = out_path / "c2_beacon_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "c2_beacon",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
