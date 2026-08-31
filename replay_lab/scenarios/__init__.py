"""Package index for Replay Lab scenario generators."""

from __future__ import annotations

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

__all__ = [
    "generate_benign_traffic",
    "generate_high_volume_legitimate",
    "generate_syn_udp_flood",
    "generate_port_scan",
    "generate_c2_beacon",
    "generate_dga_domains",
    "generate_dns_tunnel",
    "generate_encrypted_anomalies",
    "generate_large_exfiltration",
    "generate_multi_stage_killchain",
]
