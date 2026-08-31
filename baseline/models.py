"""UDT-X Behavioral Baseline Models & Data Structures.

Defines the canonical BaselineProfile representing the historical normal behavior
of a network host or destination endpoint.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaselineProfile(BaseModel):
    """Behavioral baseline profile for a host IP or destination."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    host_ip: str = Field(..., description="Target host IPv4 or IPv6 address.")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when baseline was last updated.",
    )
    total_flows_observed: int = Field(
        default=0, ge=0, description="Total flow count contributing to baseline."
    )

    # Volume statistics (bytes)
    byte_volume_mean: float = Field(
        default=0.0, ge=0.0, description="EWMA mean byte volume per flow."
    )
    byte_volume_variance: float = Field(
        default=0.0, ge=0.0, description="EWMA variance of byte volume per flow."
    )

    # Packet volume statistics
    packet_volume_mean: float = Field(
        default=0.0, ge=0.0, description="EWMA mean packets per flow."
    )

    # Historical communication partners
    known_destinations: list[str] = Field(
        default_factory=list,
        description="List of historically-seen destination IP addresses.",
    )
    known_destination_ports: list[int] = Field(
        default_factory=list,
        description="List of historically-seen destination ports.",
    )

    # Temporal & activity patterns (0-23 hours of active presence)
    active_hours: list[int] = Field(
        default_factory=list,
        description="List of hours (0-23 UTC) where host typically generates traffic.",
    )

    @property
    def byte_volume_stddev(self) -> float:
        """Standard deviation of byte volume."""
        return math.sqrt(max(0.0, self.byte_volume_variance))

    def is_normal_destination(self, dst_ip: str) -> bool:
        """Check if destination IP is part of established historical destination set."""
        if self.total_flows_observed < 5:
            return True  # Baseline warmup
        return dst_ip in self.known_destinations

    def is_normal_destination_port(self, port: int) -> bool:
        """Check if destination port is part of established historical port set."""
        if self.total_flows_observed < 5:
            return True
        return port in self.known_destination_ports

    def is_normal_hour(self, hour: int) -> bool:
        """Check if given hour is part of host's active operational hours."""
        if self.total_flows_observed < 10 or not self.active_hours:
            return True
        return hour in self.active_hours

    def volume_zscore(self, byte_count: float) -> float:
        """Calculate z-score deviation from historical byte volume baseline."""
        if self.total_flows_observed < 5:
            return 0.0
        stddev = max(self.byte_volume_stddev, self.byte_volume_mean * 0.15, 1000.0)
        return max(0.0, (byte_count - self.byte_volume_mean) / stddev)

    def is_anomalous_transfer(
        self,
        dst_ip: str,
        byte_count: float,
        hour: int | None = None,
        z_threshold: float = 3.5,
    ) -> tuple[bool, float, dict[str, Any]]:
        """Evaluate if a candidate flow is anomalous relative to baseline.

        Returns:
            (is_anomalous, anomaly_score, reasons)
        """
        if self.total_flows_observed < 5:
            return False, 0.0, {"warmup": True}

        z = self.volume_zscore(byte_count)
        is_new_dst = not self.is_normal_destination(dst_ip)
        is_off_hour = False if hour is None else not self.is_normal_hour(hour)

        reasons: dict[str, Any] = {
            "zscore": round(z, 2),
            "is_new_destination": is_new_dst,
            "is_off_hour": is_off_hour,
            "historical_mean_bytes": round(self.byte_volume_mean, 2),
        }

        # Anomaly scoring formula
        score = 0.0
        if z >= z_threshold:
            score += 0.5
        if is_new_dst:
            score += 0.3
        if is_off_hour:
            score += 0.2

        is_anom = score >= 0.5 or z >= (z_threshold + 2.0)
        return is_anom, round(min(1.0, score), 4), reasons
