"""Scenario 6: DGA algorithmic domain generation stream scenario."""

from __future__ import annotations

import json
import random
import string
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import DNSData, FlowDirection, FlowEvent, FlowSource


def generate_dga_domains(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    client_ip: str = "192.168.1.140",
    dns_server_ip: str = "8.8.8.8",
    count: int = 40,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface, target_ip=client_ip)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []
    generated_domains: list[str] = []

    tlds = [".com", ".net", ".org", ".info", ".xyz", ".top"]

    for i in range(count):
        name_len = random.randint(14, 22)
        chars = string.ascii_lowercase + string.digits
        domain_name = "".join(random.choices(chars, k=name_len))
        full_domain = f"{domain_name}{random.choice(tlds)}"
        generated_domains.append(full_domain)

        ev = FlowEvent(
            timestamp=now,
            src_ip=client_ip,
            src_port=52000 + i,
            dst_ip=dns_server_ip,
            dst_port=53,
            protocol="UDP",
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=225,
            packets=2,
            duration_ms=40.0,
            dns=DNSData(query=full_domain),
        )
        events.append(ev)

    ground_truth = {
        "scenario": "dga_domains",
        "threat_class": "DGA",
        "severity": "HIGH",
        "client_ip": client_ip,
        "queries_generated": len(events),
        "sample_domains": generated_domains[:5],
        "expected_alerts": 1,
        "mitre_technique": "T1568.002",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "dga_domains_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "dga_domains",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
