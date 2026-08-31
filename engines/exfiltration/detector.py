"""UDT-X Data Exfiltration Detection Engine — Signal Algorithms.

Inspects feature vectors for indicators of unauthorized data staging:
1. Outbound / Inbound Byte Ratio:
   - Extreme asymmetry (heavy outbound volume vs minimal inbound).
2. Destination Novelty:
   - Tracks per-host destination history. Novel destination scores high.
   - Known destinations (e.g. routine backups) score 0.0 novelty.
3. Transfer-Size Baseline Deviation:
   - Tracks host's rolling mean & standard deviation (EWMA/Z-score).
   - Significant positive standard deviation spikes flag anomalous volume.
4. Time-of-Day / Working Hours Deviation:
   - Off-hours (22:00 to 05:00 UTC) receive an off-hours multiplier.

Composite confidence score triggers Alert with threat_class="EXFILTRATION".
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Host Outbound Transfer Baseline Tracker
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class _HostExfilProfile:
    seen_destinations: set[str] = field(default_factory=set)
    mean_bytes: float = 50_000.0  # Initial default 50 KB baseline
    variance_bytes: float = (25_000.0) ** 2
    total_transfers: int = 0

    def is_novel_destination(self, dst_ip: str) -> bool:
        """Return True if host has never communicated with dst_ip before."""
        return dst_ip not in self.seen_destinations

    def record_transfer(self, dst_ip: str, outbound_bytes: float) -> None:
        """Update historical profile with observed outbound transfer."""
        self.seen_destinations.add(dst_ip)
        self.total_transfers += 1

        # Incremental Welford / EWMA update
        alpha = 0.15
        diff = outbound_bytes - self.mean_bytes
        self.mean_bytes += alpha * diff
        self.variance_bytes = (1 - alpha) * self.variance_bytes + alpha * (diff**2)

    def size_deviation_zscore(self, outbound_bytes: float) -> float:
        """Calculate z-score deviation from historical transfer size baseline."""
        stddev = max(math.sqrt(self.variance_bytes), self.mean_bytes * 0.20, 1000.0)
        z = (outbound_bytes - self.mean_bytes) / stddev
        return max(0.0, z)


# ─────────────────────────────────────────────────────────────────────────────
# Exfiltration Signals & Detector
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ExfiltrationSignals:
    ratio_score: float = 0.0
    novelty_score: float = 0.0
    size_deviation_score: float = 0.0
    time_deviation_score: float = 0.0
    confidence: float = 0.0
    is_anomaly: bool = False
    evidence: dict = field(default_factory=dict)


class ExfiltrationDetector:
    """Stateful Data Exfiltration Detector."""

    W_RATIO = 0.35
    W_NOVELTY = 0.30
    W_SIZE = 0.25
    W_TIME = 0.10

    def __init__(self) -> None:
        self._profiles: dict[str, _HostExfilProfile] = {}

    def _get_profile(self, src_ip: str) -> _HostExfilProfile:
        if src_ip not in self._profiles:
            self._profiles[src_ip] = _HostExfilProfile()
        return self._profiles[src_ip]

    def _evaluate_ratio(self, byte_ratio: float, outbound_bytes: float) -> float:
        """Score based on asymmetry and minimum transfer threshold."""
        if outbound_bytes < 100_000.0:  # Less than 100 KB is too small for exfil
            return 0.0
        # Byte ratio: normal browsing is 0.1 - 2.0 (download heavy).
        # Exfil is 10.0 to 100.0+ (upload heavy).
        if byte_ratio <= 2.0:
            return 0.0
        if byte_ratio >= 20.0:
            return 1.0
        return (byte_ratio - 2.0) / 18.0

    def _evaluate_time_of_day(self, ts: datetime) -> float:
        """Evaluate if timestamp falls in typical off-hours (22:00 - 05:00 UTC)."""
        hour = ts.hour
        # Off-hours: 22 to 23 and 0 to 5
        if hour >= 22 or hour < 5:
            return 0.8
        if hour == 21 or hour == 5:
            return 0.4
        return 0.0

    def evaluate(
        self,
        src_ip: str,
        dst_ip: str,
        outbound_bytes: float,
        inbound_bytes: float,
        byte_ratio: float,
        timestamp: datetime,
    ) -> ExfiltrationSignals:
        profile = self._get_profile(src_ip)

        # 1. Destination Novelty
        is_novel = profile.is_novel_destination(dst_ip)
        novelty_score = 1.0 if is_novel else 0.0

        # 2. Size Deviation
        z_score = profile.size_deviation_zscore(outbound_bytes)
        # Z >= 4.0 yields full size anomaly score
        size_score = min(1.0, z_score / 4.0)

        # 3. Ratio Score
        ratio_score = self._evaluate_ratio(byte_ratio, outbound_bytes)

        # 4. Time of Day Deviation
        time_score = self._evaluate_time_of_day(timestamp)

        # Composite Confidence
        confidence = (
            (self.W_RATIO * ratio_score)
            + (self.W_NOVELTY * novelty_score)
            + (self.W_SIZE * size_score)
            + (self.W_TIME * time_score)
        )

        # Update historical profile (after evaluating novelty and zscore)
        profile.record_transfer(dst_ip, outbound_bytes)

        # Exfiltration is considered an anomaly if composite confidence >= 0.50
        is_anomaly = confidence >= 0.50

        return ExfiltrationSignals(
            ratio_score=round(ratio_score, 4),
            novelty_score=novelty_score,
            size_deviation_score=round(size_score, 4),
            time_deviation_score=round(time_score, 4),
            confidence=round(float(min(1.0, confidence)), 4),
            is_anomaly=is_anomaly,
            evidence={
                "outbound_bytes": outbound_bytes,
                "inbound_bytes": inbound_bytes,
                "byte_ratio": byte_ratio,
                "is_novel_destination": is_novel,
                "size_zscore": round(z_score, 2),
                "historical_mean_bytes": round(profile.mean_bytes, 2),
                "time_of_day_hour": timestamp.hour,
                "total_host_transfers": profile.total_transfers,
            },
        )
