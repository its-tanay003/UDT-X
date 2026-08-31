"""UDT-X Reconnaissance Detection Engine — Signal Algorithms.

Implements three independent detection signals:
1. Fan-out anomaly    — one source touching an unusual number of unique
                        destination hosts or ports in the current window.
2. Sequential port scan — destination ports arriving in arithmetic sequences
                          (consistent delta ≤ 5 across recent connections).
3. Probe signature   — low bytes-per-flow / high connection-count sessions
                        that match the fingerprint of SYN/UDP probes.

Each signal produces a sub-score in [0.0, 1.0].  The composite confidence
is a weighted average; exceeding the threshold triggers an Alert.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# Sliding Port-History Window
# ─────────────────────────────────────────────────────────────────────────────


class PortHistory:
    """Maintains a capped deque of recently contacted destination ports."""

    def __init__(self, max_ports: int = 128) -> None:
        self.recent: collections.deque[int] = collections.deque(maxlen=max_ports)
        self.seen_hosts: set[str] = set()

    def add(self, dst_port: int, dst_ip: str) -> None:
        self.recent.append(dst_port)
        self.seen_hosts.add(dst_ip)

    def sequentiality_score(self) -> float:
        """
        Fraction of consecutive port pairs whose absolute difference is ≤ 5.

        A pure sequential port scan (1,2,3,4,...) returns 1.0.
        Random service traffic (80, 443, 22, 8080) returns near 0.0.
        Requires at least 4 data points to score; returns 0.0 otherwise.
        """
        ports = list(self.recent)
        if len(ports) < 4:
            return 0.0

        consecutive_pairs = sum(
            1 for a, b in zip(ports, ports[1:], strict=False) if abs(b - a) <= 5
        )
        return round(consecutive_pairs / (len(ports) - 1), 4)

    def scan_rate(self) -> float:
        """Unique ports touched per host — rough probes-per-target metric."""
        if not self.seen_hosts:
            return 0.0
        return len(self.recent) / len(self.seen_hosts)

    def reset(self) -> None:
        self.recent.clear()
        self.seen_hosts.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Recon Signals
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ReconSignals:
    """Computed sub-scores for a single FeatureVector evaluation."""

    fanout_score: float = 0.0  # Host / port fan-out sub-score
    sequential_score: float = 0.0  # Sequential-port-scan sub-score
    probe_score: float = 0.0  # Low-byte / high-conn probe sub-score
    confidence: float = 0.0  # Weighted composite
    evidence: dict = field(default_factory=dict)


class ReconDetector:
    """Stateful Reconnaissance detection engine per source IP."""

    # Composite weights
    W_FANOUT = 0.45
    W_SEQUENTIAL = 0.30
    W_PROBE = 0.25

    # Fan-out: unique destinations or ports above this triggers full score
    DST_IP_FANOUT_HIGH = 30  # hosts touched in window → 1.0
    DST_IP_FANOUT_LOW = 5  # hosts touched → score begins
    DST_PORT_FANOUT_HIGH = 50  # unique ports → 1.0
    DST_PORT_FANOUT_LOW = 8  # unique ports → score begins

    # Probe signature: bytes < this per flow and flow_count > this
    PROBE_BYTES_THRESHOLD = 200.0  # bytes per flow (mean)
    PROBE_CONN_THRESHOLD = 10  # window_flow_count
    PROBE_PACKET_MAX_SIZE = 80.0  # mean packet size (SYN = ~40 B)

    def __init__(
        self,
        src_ip: str,
        max_port_history: int = 128,
    ) -> None:
        self.src_ip = src_ip
        self.port_history = PortHistory(max_ports=max_port_history)
        self.total_flows: int = 0

    # ── Signal 1: Fan-out ────────────────────────────────────────────────────
    @staticmethod
    def _sigmoid_score(value: float, low: float, high: float) -> float:
        """Linear ramp from 0 at `low` to 1 at `high`."""
        if value <= low:
            return 0.0
        if value >= high:
            return 1.0
        return round((value - low) / (high - low), 4)

    def _fanout_score(self, unique_dst_ips: int, unique_dst_ports: int) -> float:
        ip_score = self._sigmoid_score(
            unique_dst_ips,
            self.DST_IP_FANOUT_LOW,
            self.DST_IP_FANOUT_HIGH,
        )
        port_score = self._sigmoid_score(
            unique_dst_ports,
            self.DST_PORT_FANOUT_LOW,
            self.DST_PORT_FANOUT_HIGH,
        )
        # Take the higher of the two — either host-sweep or port-sweep suffices
        return round(float(max(ip_score, port_score)), 4)

    # ── Signal 2: Sequential port-scan pattern ───────────────────────────────
    def _sequential_score(self, dst_port: int, dst_ip: str) -> float:
        self.port_history.add(dst_port, dst_ip)
        return self.port_history.sequentiality_score()

    # ── Signal 3: Probe signature ────────────────────────────────────────────
    def _probe_score(
        self,
        bytes_per_flow: float,
        window_flow_count: int,
        packet_size_mean: float,
    ) -> float:
        """Score: rises when flows are tiny AND numerous."""
        self.total_flows += 1

        # Byte-size check: SYN probes are very small
        byte_factor = max(
            0.0,
            1.0 - (bytes_per_flow / self.PROBE_BYTES_THRESHOLD),
        )

        # Connection density: many flows in the window
        conn_factor = self._sigmoid_score(
            window_flow_count,
            self.PROBE_CONN_THRESHOLD,
            self.PROBE_CONN_THRESHOLD * 5,
        )

        # Packet-size factor: tiny packets confirm probe
        pkt_factor = (
            max(
                0.0,
                1.0 - (packet_size_mean / self.PROBE_PACKET_MAX_SIZE),
            )
            if packet_size_mean > 0
            else 0.0
        )

        # All three must agree: AND-like product blended with OR-like max
        score = (byte_factor * conn_factor * 0.6) + (pkt_factor * 0.4)
        return round(float(min(1.0, score)), 4)

    # ── Composite evaluator ──────────────────────────────────────────────────
    def evaluate(
        self,
        dst_ip: str,
        dst_port: int,
        unique_dst_ips: int,
        unique_dst_ports: int,
        bytes_per_flow: float,
        window_flow_count: int,
        packet_size_mean: float,
        scan_rate_override: float | None = None,
    ) -> ReconSignals:
        fanout = self._fanout_score(unique_dst_ips, unique_dst_ports)
        seq = self._sequential_score(dst_port, dst_ip)
        probe = self._probe_score(bytes_per_flow, window_flow_count, packet_size_mean)

        confidence = (
            self.W_FANOUT * fanout + self.W_SEQUENTIAL * seq + self.W_PROBE * probe
        )

        scan_rate = scan_rate_override or self.port_history.scan_rate()

        return ReconSignals(
            fanout_score=fanout,
            sequential_score=seq,
            probe_score=probe,
            confidence=round(float(min(1.0, confidence)), 4),
            evidence={
                "unique_dst_ips": unique_dst_ips,
                "unique_dst_ports": unique_dst_ports,
                "fan_out_count": max(unique_dst_ips, unique_dst_ports),
                "scan_rate": round(scan_rate, 2),
                "sequentiality_score": seq,
                "bytes_per_flow": round(bytes_per_flow, 2),
                "window_flow_count": window_flow_count,
                "packet_size_mean": round(packet_size_mean, 2),
                "total_flows_seen": self.total_flows,
                "ports_in_history": len(self.port_history.recent),
            },
        )
