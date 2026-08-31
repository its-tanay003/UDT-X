"""Tests for Phase 12 Replay Lab & Attack Scenarios."""

from __future__ import annotations

import pytest

from replay_lab.runner import run_scenario
from replay_lab.safety import ProductionInterfaceSafetyError, validate_lab_environment


def test_safety_guard_blocks_production_interface():
    """Verify safety guard blocks production interface names."""
    with pytest.raises(ProductionInterfaceSafetyError):
        validate_lab_environment(target_interface="eth0")

    with pytest.raises(ProductionInterfaceSafetyError):
        validate_lab_environment(target_interface="enp3s0")


def test_safety_guard_allows_loopback_and_lab():
    """Verify safety guard permits isolated lab/loopback interfaces."""
    validate_lab_environment(target_interface="127.0.0.1")
    validate_lab_environment(target_interface="lo")
    validate_lab_environment(target_interface="udtx-lab")


def test_all_scenarios_generate_events_and_ground_truth(tmp_path):
    """Verify all 10 scenario generators produce valid events and ground truth files."""
    test_scenarios = [
        "benign",
        "high_volume_legitimate",
        "syn_udp_flood",
        "port_scan",
        "c2_beacon",
        "dga_domains",
        "dns_tunnel",
        "encrypted_anomalies",
        "large_exfiltration",
        "multi_stage_killchain",
    ]

    for sc in test_scenarios:
        res = run_scenario(
            scenario_name=sc,
            target_interface="127.0.0.1",
            output_dir=str(tmp_path),
        )
        assert "scenario" in res
        assert "events" in res
        assert len(res["events"]) > 0
        assert "ground_truth" in res
        assert "created_at" in res["ground_truth"]
