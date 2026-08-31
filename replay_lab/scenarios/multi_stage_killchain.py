"""Scenario 10: Multi-Stage APT Attack Chain.

Progression: Recon -> C2 Beacon -> Exfiltration.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from replay_lab.safety import validate_lab_environment
from schema.models import FlowDirection, FlowEvent, FlowSource, TLSData


def generate_multi_stage_killchain(
    output_dir: Path | str = "data/scenarios",
    target_interface: str = "127.0.0.1",
    attacker_victim_ip: str = "192.168.1.105",
    internal_gateway_ip: str = "10.0.0.1",
    c2_server_ip: str = "198.51.100.22",
) -> dict[str, Any]:
    validate_lab_environment(
        target_interface=target_interface, target_ip=attacker_victim_ip
    )
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    base_time = datetime.now(UTC) - timedelta(minutes=15)
    events: list[FlowEvent] = []

    # Phase 1: Reconnaissance
    probe_ports = [22, 80, 443, 445, 3389, 8080, 8443, 9000]
    for idx, port in enumerate(probe_ports):
        ev_recon = FlowEvent(
            timestamp=base_time + timedelta(seconds=idx * 2),
            src_ip=attacker_victim_ip,
            src_port=55000 + idx,
            dst_ip=internal_gateway_ip,
            dst_port=port,
            protocol="TCP",
            direction=FlowDirection.INTERNAL,
            source=FlowSource.ZEEK,
            bytes=44,
            packets=1,
            duration_ms=1.0,
        )
        events.append(ev_recon)

    # Phase 2: C2 Beaconing Channel Established
    for idx in range(12):
        ev_c2 = FlowEvent(
            timestamp=base_time + timedelta(minutes=5, seconds=idx * 10),
            src_ip=attacker_victim_ip,
            src_port=56000 + idx,
            dst_ip=c2_server_ip,
            dst_port=443,
            protocol="TCP",
            direction=FlowDirection.OUTBOUND,
            source=FlowSource.ZEEK,
            bytes=600,
            packets=8,
            duration_ms=80.0,
            tls=TLSData(
                ja3="e7d705a3286e19ea42f587b344ee6865",
                sni="apt-c2-channel.threat-infra.net",
            ),
        )
        events.append(ev_c2)

    # Phase 3: Outbound Asymmetric Data Exfiltration
    ev_exfil = FlowEvent(
        timestamp=base_time + timedelta(minutes=12),
        src_ip=attacker_victim_ip,
        src_port=57000,
        dst_ip=c2_server_ip,
        dst_port=443,
        protocol="TCP",
        direction=FlowDirection.OUTBOUND,
        source=FlowSource.ZEEK,
        bytes=5458200,
        packets=3960,
        duration_ms=14200.0,
        tls=TLSData(
            ja3="e7d705a3286e19ea42f587b344ee6865",
            sni="apt-c2-channel.threat-infra.net",
        ),
    )
    events.append(ev_exfil)

    ground_truth = {
        "scenario": "multi_stage_killchain",
        "threat_classes": ["RECONNAISSANCE", "C2_BEACONING", "EXFILTRATION"],
        "attack_chain": "RECONNAISSANCE -> C2_BEACONING -> EXFILTRATION",
        "severity": "CRITICAL",
        "victim_host_ip": attacker_victim_ip,
        "c2_server_ip": c2_server_ip,
        "expected_incident": True,
        "expected_alerts_count": 3,
        "mitre_techniques": ["T1046", "T1071.004", "T1048"],
        "created_at": base_time.isoformat(),
    }

    gt_file = out_path / "multi_stage_killchain_ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as fp:
        json.dump(ground_truth, fp, indent=2)

    return {
        "scenario": "multi_stage_killchain",
        "events": [e.model_dump(mode="json") for e in events],
        "ground_truth": ground_truth,
        "ground_truth_file": str(gt_file),
    }
