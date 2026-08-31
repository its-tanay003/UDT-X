"""Scenario 8: Encrypted session anomaly.

Uses varying JA3 fingerprints & self-signed certificates.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource, TLSData


def generate_encrypted_anomalies(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    client_ip: str = "192.168.1.160",
    external_ip: str = "198.51.100.99",
    count: int = 20,
) -> dict[str, Any]:
    validate_lab_environment(target_interface=target_interface, target_ip=client_ip)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    events: list[FlowEvent] = []

    ja3_signatures = [
        ("6734f37431670b3ab4292b8f60f29984", "malicious.c2-relay.net"),
        ("a0e9f5d64349fb13191bc781f81f42e1", "dark-payload.services-host.xyz"),
        ("b3846467362a7b8e5c1411516e87f174", "shadow-ingress.net"),
    ]

    for i in range(count):
        ja3_hash, sni = ja3_signatures[i % len(ja3_signatures)]
        ev = FlowEvent(
            timestamp=now,
            src_ip=client_ip,
            src_port=51000 + i,
            dst_ip=external_ip,
            dst_port=443,
            protocol="TLS",
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=5120 + (i * 256),
            packets=28,
            duration_ms=2400.0,
            tls=TLSData(
                ja3=ja3_hash,
                sni=sni,
                cipher="TLS_RSA_WITH_AES_256_CBC_SHA",
            ),
        )
        events.append(ev)

    ground_truth = {
        "scenario": "encrypted_anomalies",
        "threat_class": "ENCRYPTED_ANOMALY",
        "severity": "MEDIUM",
        "client_ip": client_ip,
        "external_ip": external_ip,
        "ja3_evaluated": len(events),
        "expected_alerts": 1,
        "mitre_technique": "T1573.002",
        "created_at": now.isoformat(),
    }

    gt_file = out_path / "encrypted_anomalies_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "encrypted_anomalies",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
