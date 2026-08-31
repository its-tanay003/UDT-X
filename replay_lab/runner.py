"""Replay Lab Execution Runner.

Provides programmatic execution of all 10 benign and attack scenarios,
safety validation, and direct callable integration for FastAPI /replay endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from replay_lab.safety import validate_lab_environment
from replay_lab.scenarios.benign_traffic import generate_benign_traffic
from replay_lab.scenarios.c2_beacon import generate_c2_beacon
from replay_lab.scenarios.dga_domains import generate_dga_domains
from replay_lab.scenarios.dns_tunnel import generate_dns_tunnel
from replay_lab.scenarios.encrypted_anomalies import generate_encrypted_anomalies
from replay_lab.scenarios.high_volume_legitimate import generate_high_volume_legitimate
from replay_lab.scenarios.large_exfiltration import generate_large_exfiltration
from replay_lab.scenarios.multi_stage_killchain import generate_multi_stage_killchain
from replay_lab.scenarios.port_scan import generate_port_scan
from replay_lab.scenarios.syn_udp_flood import generate_syn_udp_flood

logger = logging.getLogger("udtx.replay_lab.runner")

SCENARIO_MAP = {
    "benign": generate_benign_traffic,
    "benign_traffic": generate_benign_traffic,
    "high_volume_legitimate": generate_high_volume_legitimate,
    "syn_udp_flood": generate_syn_udp_flood,
    "ddos_surge": generate_syn_udp_flood,
    "port_scan": generate_port_scan,
    "c2_beacon": generate_c2_beacon,
    "dga_domains": generate_dga_domains,
    "dga_c2": generate_dga_domains,
    "dns_tunnel": generate_dns_tunnel,
    "encrypted_anomalies": generate_encrypted_anomalies,
    "encrypted_anomaly": generate_encrypted_anomalies,
    "large_exfiltration": generate_large_exfiltration,
    "exfil_spike": generate_large_exfiltration,
    "multi_stage_killchain": generate_multi_stage_killchain,
    "kill_chain": generate_multi_stage_killchain,
}


def run_scenario(
    scenario_name: str,
    target_interface: str = "127.0.0.1",
    output_dir: str = "data/scenarios",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute scenario generator with strict lab isolation guard."""
    validate_lab_environment(target_interface=target_interface)

    scenario_key = scenario_name.lower().strip()
    generator_func = SCENARIO_MAP.get(scenario_key)

    if generator_func is None:
        valid_keys = sorted(set(SCENARIO_MAP.keys()))
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. Available: {valid_keys}"
        )

    logger.info(
        "Executing Replay Lab scenario: %s on interface: %s",
        scenario_name,
        target_interface,
    )
    return generator_func(
        output_dir=output_dir, target_interface=target_interface, **kwargs
    )
