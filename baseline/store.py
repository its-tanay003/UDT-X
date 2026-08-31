"""UDT-X Behavioral Baseline In-Memory and Redis State Store.

Maintains real-time per-host EWMA volume statistics, destination sets,
and active hours with automatic Redis persistence and in-memory fallback.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from baseline.models import BaselineProfile
from schema.models import FlowEvent

logger = logging.getLogger("udtx.baseline.store")


class BaselineStore:
    """Per-host behavioral baseline storage engine backed by Redis or local memory."""

    PREFIX = "udtx:baseline:"
    ALPHA = 0.10  # EWMA smoothing factor

    def __init__(self, redis_client: Any | None = None) -> None:
        self.redis = redis_client
        self._memory_store: dict[str, BaselineProfile] = {}

    def get_profile(self, host_ip: str) -> BaselineProfile:
        """Fetch current BaselineProfile for given host_ip."""
        # 1. Try Redis
        if self.redis is not None:
            try:
                raw = self.redis.get(f"{self.PREFIX}{host_ip}")
                if raw:
                    raw_str = raw if isinstance(raw, str) else raw.decode("utf-8")
                    data = json.loads(raw_str)
                    return BaselineProfile.model_validate(data)
            except Exception as exc:
                logger.warning("Failed to fetch baseline profile from Redis: %s", exc)

        # 2. In-memory fallback
        if host_ip not in self._memory_store:
            self._memory_store[host_ip] = BaselineProfile(host_ip=host_ip)
        return self._memory_store[host_ip]

    def update_from_flow(self, flow: FlowEvent) -> BaselineProfile:
        """Incrementally update baseline profile with incoming FlowEvent."""
        profile = self.get_profile(flow.src_ip)

        flow_bytes = float(flow.bytes)
        flow_packets = float(flow.packets)
        hour = flow.timestamp.hour

        # 1. Update volume EWMA
        if profile.total_flows_observed == 0:
            profile.byte_volume_mean = flow_bytes
            profile.byte_volume_variance = (flow_bytes * 0.25) ** 2
            profile.packet_volume_mean = flow_packets
        else:
            diff = flow_bytes - profile.byte_volume_mean
            profile.byte_volume_mean += self.ALPHA * diff
            profile.byte_volume_variance = (
                1.0 - self.ALPHA
            ) * profile.byte_volume_variance + self.ALPHA * (diff**2)
            profile.packet_volume_mean += self.ALPHA * (
                flow_packets - profile.packet_volume_mean
            )

        # 2. Update destination history (cap at 200 items)
        if flow.dst_ip not in profile.known_destinations:
            profile.known_destinations.append(flow.dst_ip)
            if len(profile.known_destinations) > 200:
                profile.known_destinations.pop(0)

        # 3. Update destination port history (cap at 100 items)
        if flow.dst_port not in profile.known_destination_ports:
            profile.known_destination_ports.append(flow.dst_port)
            if len(profile.known_destination_ports) > 100:
                profile.known_destination_ports.pop(0)

        # 4. Update active hours
        if hour not in profile.active_hours:
            profile.active_hours.append(hour)
            profile.active_hours.sort()

        profile.total_flows_observed += 1
        profile.last_updated = flow.timestamp

        # Save profile
        self.save_profile(profile)
        return profile

    def save_profile(self, profile: BaselineProfile) -> None:
        """Persist profile to Redis and local memory."""
        self._memory_store[profile.host_ip] = profile
        if self.redis is not None:
            try:
                key = f"{self.PREFIX}{profile.host_ip}"
                self.redis.set(key, profile.model_dump_json())
            except Exception as exc:
                logger.warning("Failed to persist baseline to Redis: %s", exc)

    def all_profiles(self) -> list[BaselineProfile]:
        """Return all active host profiles."""
        return list(self._memory_store.values())
