"""Scenario 9: Controlled large outbound data transfer / exfiltration burst."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource, TLSData


def generate_large_exfiltration(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    source_host_ip: str = "192.168.1.180",
    external_sink_ip: str = "203.0.113.88",
    total_bytes_mb: float = 8.4,
) -> dict[str, Any]:
    validate_lab_environment(
        target_interface=target_interface, target_ip=source_host_ip
    )
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    bytes_in = int(total_bytes_mb * 1024 * 1024)

    ev = FlowEvent(
        timestamp=now,
        src_ip=source_host_ip,
        src_port=49200,
        dst_ip=external_sink_ip,
        dst_port=443,
        protocol="TCP",
        direction=FlowDirection.OUTBOUND,
        source=FlowSource.ZEEK,
        bytes=bytes_in,
        packets=6540,
        duration_ms=18500.0,
        tls=TLSData(
            ja3="3b5074b1b1e014eabda672e2e4c7d428",
            sni="s3-backup-storage.cloud-sync.org",
        ),
    )
    events.append(ev)

    ground_truth = {
        "scenario": "large_exfiltration",
        "threat_class": "EXFILTRATION",
        "severity": "CRITICAL",
        "source_host_ip": source_host_ip,
        "external_sink_ip": external_sink_ip,
        "exfiltrated_bytes": bytes_in,
        "baseline_sigma_deviation": "+5.4σ",
        "expected_alerts": 1,
        "mitre_technique": "T1048",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "large_exfiltration_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "large_exfiltration",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
