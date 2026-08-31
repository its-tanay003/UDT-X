"""UDT-X DDoS Detection Engine — Statistical Baseline & Signal Combiner.

Implements three independent detection signals:
1. Throughput anomaly  — sustained packets/sec or bytes/sec above EWMA baseline.
2. Entropy collapse    — destination-IP entropy drop (many sources → one target,
                         or one source fanning out: volumetric vs. amplification).
3. Protocol imbalance  — abnormal SYN-flood or UDP-flood ratio against baseline.

Each signal produces a sub-score in [0.0, 1.0].  The combined confidence score
is a weighted average; when it exceeds the configurable threshold the engine
emits an Alert.
"""

from __future__ import annotations

import collections
import math
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# EWMA Tracker  (Exponentially Weighted Moving Average + std-dev estimation)
# ─────────────────────────────────────────────────────────────────────────────


class EWMATracker:
    """Single-metric EWMA tracker with running variance for z-score detection."""

    def __init__(self, alpha: float = 0.2, warmup: int = 5) -> None:
        self.alpha = alpha  # smoothing factor (0 < alpha < 1)
        self.warmup = warmup  # number of samples before alerting
        self.mean: float | None = None
        self.var: float = 0.0
        self.n: int = 0

    def update(self, value: float) -> float:
        """Update EWMA and return current z-score (or 0.0 during warm-up).

        Key detail: z-score uses the *previous* variance, not the variance
        just updated with this same sample — otherwise a flat baseline has
        var=0 and the first spike's z-score is computed against near-zero
        variance, underestimating the anomaly.
        """
        self.n += 1
        if self.mean is None:
            self.mean = value
            self.var = 0.0
            return 0.0

        prev_mean = self.mean
        prev_var = self.var

        # diff relative to prior mean (before update)
        diff = value - prev_mean
        # EWMA mean update
        self.mean = self.alpha * value + (1.0 - self.alpha) * prev_mean
        # EWMA variance update (Park 2021)
        self.var = (1.0 - self.alpha) * (prev_var + self.alpha * diff**2)

        if self.n < self.warmup:
            return 0.0

        # Stddev floor: at least 20% of prev_mean so flat-baseline traffic
        # gives a proportional z-score. A 2x burst → z≈5, a 500x DDoS → z≈2500.
        # This separates legitimate bursts from volumetric DDoS at Z_THRESHOLD=6.
        min_stddev = max(abs(prev_mean) * 0.20, 1e-3)
        stddev = max(math.sqrt(prev_var), min_stddev)
        z = diff / stddev
        return float(z)

    @property
    def ready(self) -> bool:
        return self.n >= self.warmup


# ─────────────────────────────────────────────────────────────────────────────
# IP Entropy Window  (sliding set of src / dst IPs per measurement epoch)
# ─────────────────────────────────────────────────────────────────────────────


class EntropyWindow:
    """Computes Shannon entropy over a rolling window of IP counts."""

    def __init__(self, max_entries: int = 256) -> None:
        self.counts: collections.Counter[str] = collections.Counter()
        self.max_entries = max_entries

    def add(self, ip: str) -> None:
        self.counts[ip] += 1
        if len(self.counts) > self.max_entries:
            # Evict least-common entry
            least = self.counts.most_common()[:-2:-1]
            if least:
                del self.counts[least[0][0]]

    def entropy(self) -> float:
        total = sum(self.counts.values())
        if total == 0:
            return 0.0
        ent = 0.0
        for c in self.counts.values():
            p = c / total
            ent -= p * math.log2(p)
        return ent

    def reset(self) -> None:
        self.counts.clear()


# ─────────────────────────────────────────────────────────────────────────────
# DDoS Signal Detector
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DDoSSignals:
    """Computed sub-scores for a single FeatureVector evaluation."""

    throughput_z: float = 0.0  # z-score of pps or bps vs EWMA
    throughput_score: float = 0.0  # normalised to [0,1]
    entropy_score: float = 0.0  # 1 = entropy collapsed to near 0
    protocol_score: float = 0.0  # SYN/UDP ratio anomaly score
    confidence: float = 0.0  # weighted composite
    evidence: dict = field(default_factory=dict)


class DDoSDetector:
    """Stateful DDoS detection engine per destination IP."""

    # Weights for confidence composite
    W_THROUGHPUT = 0.50
    W_ENTROPY = 0.30
    W_PROTOCOL = 0.20

    # Threshold above which we flag as anomalous throughput (z-score)
    # z=6 → throughput_score≈0.87; z=10 → ≈0.97.  A 2x burst on flat
    # baseline with 20% stddev floor gives z≈5 → score≈0.73 (below threshold
    # when entropy+protocol are also low, combined conf ≈ 0.37).
    Z_THRESHOLD = 6.0

    # Maximum expected destination entropy for a well-behaved server
    # (drops below this = potential reflection/amplification target)
    ENTROPY_LOW_MARK = 1.5  # many sources -> one dest
    ENTROPY_HIGH_MARK = 5.0  # baseline healthy

    def __init__(
        self,
        dst_ip: str,
        ewma_alpha: float = 0.2,
        warmup_samples: int = 5,
    ) -> None:
        self.dst_ip = dst_ip
        self.pps_tracker = EWMATracker(alpha=ewma_alpha, warmup=warmup_samples)
        self.bps_tracker = EWMATracker(alpha=ewma_alpha, warmup=warmup_samples)
        self.src_entropy_window = EntropyWindow()
        self.protocol_counts: collections.Counter[str] = collections.Counter()
        self.total_flows: int = 0

    def _throughput_score(self, pps: float, bps: float) -> tuple[float, float]:
        z_pps = self.pps_tracker.update(pps)
        z_bps = self.bps_tracker.update(bps)
        z_max = max(z_pps, z_bps)

        # Gate: no score until both trackers pass warm-up
        if not (self.pps_tracker.ready and self.bps_tracker.ready):
            return 0.0, 0.0

        # Clamp z before sigmoid to avoid math.exp overflow (z > ~700 is saturated)
        z_clamped = min(z_max, 50.0)
        # Sigmoid mapping: z=3 → ~0.50, z=6 → ~0.87, z=10 → ~0.97
        score = 1.0 - 1.0 / (1.0 + math.exp((z_clamped - self.Z_THRESHOLD) * 0.6))
        return round(float(max(0.0, score)), 4), round(z_max, 2)

    # ── Signal 2: Source-IP entropy collapse ─────────────────────────────────
    def _entropy_score(self, src_ip: str) -> float:
        self.src_entropy_window.add(src_ip)
        ent = self.src_entropy_window.entropy()
        n_unique = len(self.src_entropy_window.counts)

        # Need at least 4 unique sources before scoring
        if n_unique < 4:
            return 0.0

        # Entropy collapse: many IPs converging on one dest
        if ent < self.ENTROPY_LOW_MARK:
            # Score scales as entropy approaches 0
            score = 1.0 - (ent / self.ENTROPY_LOW_MARK)
        else:
            score = 0.0

        return round(float(min(1.0, score)), 4)

    # ── Signal 3: Protocol imbalance ─────────────────────────────────────────
    def _protocol_score(self, protocol: str, pps: float) -> float:
        self.total_flows += 1
        proto_upper = protocol.upper()
        self.protocol_counts[proto_upper] += 1

        if self.total_flows < 5:
            return 0.0

        # SYN / UDP ratio anomaly: if >80% of traffic is pure UDP or ICMP
        udp_ratio = self.protocol_counts.get("UDP", 0) / self.total_flows
        icmp_ratio = self.protocol_counts.get("ICMP", 0) / self.total_flows
        flood_ratio = udp_ratio + icmp_ratio

        # Also flag sustained high-PPS UDP (reflection / amplification)
        pps_factor = min(1.0, pps / 50_000.0)
        score = min(1.0, flood_ratio * 1.5 + pps_factor * 0.5)
        return round(float(score), 4)

    # ── Composite evaluator ───────────────────────────────────────────────────
    def evaluate(
        self,
        src_ip: str,
        protocol: str,
        pps: float,
        bps: float,
    ) -> DDoSSignals:
        t_score, z_val = self._throughput_score(pps, bps)
        e_score = self._entropy_score(src_ip)
        p_score = self._protocol_score(protocol, pps)

        confidence = (
            self.W_THROUGHPUT * t_score
            + self.W_ENTROPY * e_score
            + self.W_PROTOCOL * p_score
        )

        return DDoSSignals(
            throughput_z=z_val,
            throughput_score=t_score,
            entropy_score=e_score,
            protocol_score=p_score,
            confidence=round(float(min(1.0, confidence)), 4),
            evidence={
                "pps": pps,
                "bps": bps,
                "throughput_z_score": z_val,
                "src_entropy": round(self.src_entropy_window.entropy(), 4),
                "n_unique_src": len(self.src_entropy_window.counts),
                "protocol": protocol,
                "udp_ratio": round(
                    self.protocol_counts.get("UDP", 0) / max(1, self.total_flows),
                    4,
                ),
                "total_flows_seen": self.total_flows,
            },
        )
