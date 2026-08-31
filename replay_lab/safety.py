"""Safety interface guard for UDT-X Replay Lab.

Refuses to emit packets or execute simulations against non-isolated interfaces.
"""

from __future__ import annotations

import os
import re

SAFE_INTERFACES = {
    "lo",
    "lo0",
    "loopback",
    "127.0.0.1",
    "localhost",
    "::1",
    "udtx-lab",
    "udtx_isolated_bridge",
    "docker0",
    "br-udtx",
}

SAFE_IP_PATTERNS = [
    re.compile(r"^127\.\d+\.\d+\.\d+$"),
    re.compile(r"^192\.168\.1\.\d+$"),
    re.compile(r"^10\.0\.\d+\.\d+$"),
    re.compile(r"^198\.51\.100\.\d+$"),  # RFC 5737 Test-Net-2
    re.compile(r"^203\.0\.113\.\d+$"),   # RFC 5737 Test-Net-3
    re.compile(r"^8\.8\.8\.8$"),          # Safe public simulation sink
]


class ProductionInterfaceSafetyError(RuntimeError):
    """Raised when an unsafe or non-lab interface/target is detected."""


def validate_lab_environment(
    target_interface: str | None = None,
    target_ip: str | None = None,
) -> None:
    """Validate that simulation traffic is strictly confined to lab interfaces."""
    # Check environment override
    allow_all = os.getenv("UDTX_ALLOW_NON_LAB", "false").lower() == "true"
    if allow_all:
        return

    if target_interface:
        norm_iface = target_interface.lower().strip()
        is_lab_prefix = norm_iface.startswith(("lo", "lab-", "udtx-"))
        if norm_iface not in SAFE_INTERFACES and not is_lab_prefix:
            allowed_list = sorted(SAFE_INTERFACES)
            raise ProductionInterfaceSafetyError(
                f"SAFETY SHUTDOWN: Target interface '{target_interface}' is not "
                f"an authorized isolated lab interface! Allowed: {allowed_list}"
            )

    if target_ip:
        if not any(pattern.match(target_ip) for pattern in SAFE_IP_PATTERNS):
            raise ProductionInterfaceSafetyError(
                f"SAFETY SHUTDOWN: Target IP '{target_ip}' is outside authorized "
                "lab simulation subnet range!"
            )
