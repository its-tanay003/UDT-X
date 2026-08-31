"""Scenario 1: Benign HTTP/API and DNS background traffic."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import DNSData, FlowDirection, FlowEvent, FlowSource


def generate_benign_traffic(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    count: int = 50,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    user_ips = ["192.168.1.50", "192.168.1.51", "192.168.1.52"]
    services = [
        ("10.0.0.80", 80, "TCP", "api.internal.corp"),
        ("10.0.0.43", 443, "TCP", "portal.internal.corp"),
        ("8.8.8.8", 53, "UDP", "dns.google"),
    ]

    for i in range(count):
        src_ip = user_ips[i % len(user_ips)]
        dst_ip, dst_port, proto, domain = services[i % len(services)]

        ev = FlowEvent(
            timestamp=now,
            src_ip=src_ip,
            src_port=49152 + (i * 2),
            dst_ip=dst_ip,
            dst_port=dst_port,
            protocol=proto,
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=1770 + (i * 17),
            packets=20,
            duration_ms=450.0,
            dns=DNSData(query=domain) if proto == "UDP" else None,
        )
        events.append(ev)

    ground_truth = {
        "scenario": "benign_web_api",
        "label": "BENIGN",
        "expected_alerts": 0,
        "event_count": len(events),
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "benign_web_api_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "benign_web_api",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
