"""UDT-X C2 Beaconing Detection Engine — Signal Algorithms.

Implements three independent detection signals:

1. Periodicity × Jitter (beacon heartbeat)
   Combines the autocorrelation-based `periodicity_score` from TemporalFeatures
   with the inverse of `jitter_ms`.  A true beacon is *strictly* regular;
   normal polling services have jitter in the hundreds of milliseconds because
   they wait for application-layer round-trips.

2. Destination Persistence
   Tracks every (src_ip → dst_ip) pair.  A C2 beacon contacts the *same*
   remote IP repeatedly over an extended observation window.  Score scales
   with contact count and observation-window duration.

3. Small / Consistent Payload
   C2 keep-alive beacons carry minimal data — typically 40–150 bytes.
   Legitimate health-check endpoints return HTTP bodies, JSON payloads, or
   TLS record headers that push mean packet size above 400–1000 bytes.
   Score is higher when `packet_size_mean` is small AND `packet_size_stddev`
   is small relative to the mean (low coefficient of variation).

Composite confidence = 0.45 × periodicity_score
                     + 0.35 × persistence_score
                     + 0.20 × payload_score

Threshold for C2 alert emission: 0.50  (configurable).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# Destination Persistence Tracker
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class _PersistenceRecord:
    first_seen: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    contacts: int = 0

    def observe(self, now: float | None = None) -> None:
        if now is None:
            now = time.monotonic()
        if self.contacts == 0:
            self.first_seen = now
        self.last_seen = now
        self.contacts += 1

    def duration_secs(self) -> float:
        return max(0.0, self.last_seen - self.first_seen)


class PersistenceTracker:
    """Per-(src, dst) contact counter with monotonic-time awareness."""

    # Contact count ramp
    CONTACT_LOW = 5
    CONTACT_HIGH = 25

    # Observation-window ramp (seconds)
    WINDOW_LOW = 30.0  # 30 s → score starts rising
    WINDOW_HIGH = 900.0  # 15 min → full persistence score

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], _PersistenceRecord] = {}

    def observe(
        self,
        src_ip: str,
        dst_ip: str,
        now: float | None = None,
    ) -> _PersistenceRecord:
        key = (src_ip, dst_ip)
        if key not in self._records:
            self._records[key] = _PersistenceRecord()
        rec = self._records[key]
        rec.observe(now)
        return rec

    def score(self, src_ip: str, dst_ip: str) -> float:
        """Return a [0.0, 1.0] persistence score for this src→dst pair."""
        key = (src_ip, dst_ip)
        if key not in self._records:
            return 0.0
        rec = self._records[key]

        contact_score = _ramp(rec.contacts, self.CONTACT_LOW, self.CONTACT_HIGH)
        window_score = _ramp(rec.duration_secs(), self.WINDOW_LOW, self.WINDOW_HIGH)

        # Both factors must be non-zero — neither alone is sufficient
        if contact_score == 0.0 or window_score == 0.0:
            return 0.0

        combined = contact_score * 0.6 + window_score * 0.4
        return round(float(min(1.0, combined)), 4)

    def record(self, src_ip: str, dst_ip: str) -> _PersistenceRecord | None:
        return self._records.get((src_ip, dst_ip))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _ramp(value: float, low: float, high: float) -> float:
    """Linear ramp: 0 at `low`, 1 at `high`."""
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


# ─────────────────────────────────────────────────────────────────────────────
# Beacon Signals Dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class BeaconSignals:
    periodicity_score: float = 0.0  # Signal 1: high periodicity, low jitter
    persistence_score: float = 0.0  # Signal 2: long-lived dst contact
    payload_score: float = 0.0  # Signal 3: small / consistent payload
    confidence: float = 0.0  # Weighted composite
    contact_count: int = 0
    observation_secs: float = 0.0
    evidence: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# C2 Beacon Detector
# ─────────────────────────────────────────────────────────────────────────────


class C2BeaconDetector:
    """Stateful C2 Beaconing Detector.

    Maintains a shared `PersistenceTracker` across all (src, dst) pairs.
    Accepts one FeatureVector at a time via `evaluate()`.
    """

    # Composite weights
    W_PERIODICITY = 0.45
    W_PERSISTENCE = 0.35
    W_PAYLOAD = 0.20

    # ── Signal 1 thresholds ─────────────────────────────────────────────────
    # Periodicity score threshold — only score above this level
    PERIODICITY_LOW = 0.65  # score begins (raised from 0.50)
    PERIODICITY_HIGH = 0.90  # full score

    # Jitter gating: above JITTER_MAX → zero jitter bonus
    # This is the primary differentiator vs. legitimate polling services:
    # a Kubernetes scraper with 300 ms RTT jitter scores 0 on the jitter axis.
    JITTER_MAX_MS = 250.0  # above this → no jitter bonus (tightened from 500)
    JITTER_IDEAL_MS = 10.0  # below this → full jitter bonus

    # ── Signal 3 thresholds ─────────────────────────────────────────────────
    # Mean packet size: small packets → beacon, large → data transfer
    PAYLOAD_BYTES_LOW = 40.0  # below → full score
    PAYLOAD_BYTES_HIGH = 300.0  # above → zero size component (tightened from 400)

    # Coefficient of variation: low CV = consistent payload = beacon
    CV_LOW = 0.05  # ≤ 5 % → full cv_bonus
    CV_HIGH = 0.35  # ≥ 35 % → no cv_bonus (tightened from 0.50)

    def __init__(self) -> None:
        self.tracker = PersistenceTracker()

    # ── Signal 1: Periodicity × Jitter ──────────────────────────────────────
    def _periodicity_signal(
        self,
        periodicity_score: float,
        jitter_ms: float,
    ) -> float:
        """
        Combines raw periodicity score with a jitter-based multiplier.

        A strict beacon has jitter in single-digit milliseconds.
        A normal application timer (e.g. HTTP keep-alive) has jitter in the
        hundreds of milliseconds due to OS scheduling + network RTT variance.
        """
        p_score = _ramp(periodicity_score, self.PERIODICITY_LOW, self.PERIODICITY_HIGH)

        # Jitter multiplier: 1.0 when jitter ≤ IDEAL, 0.0 when ≥ MAX
        jitter_factor = max(
            0.0,
            (self.JITTER_MAX_MS - jitter_ms)
            / (self.JITTER_MAX_MS - self.JITTER_IDEAL_MS),
        )
        jitter_factor = min(1.0, jitter_factor)

        # Blend: periodicity alone (0.7) + jitter bonus (0.3)
        return round(float(p_score * 0.70 + jitter_factor * p_score * 0.30), 4)

    # ── Signal 3: Small / Consistent Payload ────────────────────────────────
    def _payload_signal(
        self,
        packet_size_mean: float,
        packet_size_stddev: float,
    ) -> float:
        """Score rises when mean is small AND coefficient of variation is low."""
        # Size factor: inverse ramp — small packets score high
        size_factor = max(
            0.0,
            1.0
            - _ramp(
                packet_size_mean,
                self.PAYLOAD_BYTES_LOW,
                self.PAYLOAD_BYTES_HIGH,
            ),
        )

        # CV factor: low variation → consistent beacon size
        cv = (packet_size_stddev / packet_size_mean) if packet_size_mean > 0 else 0.0
        cv_factor = max(0.0, 1.0 - _ramp(cv, self.CV_LOW, self.CV_HIGH))

        # Both must agree
        return round(float(size_factor * 0.65 + cv_factor * 0.35), 4)

    # ── Composite evaluator ──────────────────────────────────────────────────
    def evaluate(
        self,
        src_ip: str,
        dst_ip: str,
        periodicity_score: float,
        jitter_ms: float,
        packet_size_mean: float,
        packet_size_stddev: float,
        now: float | None = None,
    ) -> BeaconSignals:
        # Update persistence state
        rec = self.tracker.observe(src_ip, dst_ip, now=now)

        # Compute sub-scores
        p_signal = self._periodicity_signal(periodicity_score, jitter_ms)
        payload = self._payload_signal(packet_size_mean, packet_size_stddev)

        # Persistence credit only flows when periodicity is already strong.
        # Gate = 0.55 means:
        #   - High-jitter poller (300 ms jitter, p_signal ≈ 0.48) → gate closed
        #   - True C2 beacon (3 ms jitter, p_signal ≈ 0.87+)      → gate open
        if p_signal >= 0.55:
            persistence = self.tracker.score(src_ip, dst_ip)
        else:
            persistence = 0.0

        confidence = (
            self.W_PERIODICITY * p_signal
            + self.W_PERSISTENCE * persistence
            + self.W_PAYLOAD * payload
        )

        cv = (packet_size_stddev / packet_size_mean) if packet_size_mean > 0 else 0.0

        return BeaconSignals(
            periodicity_score=p_signal,
            persistence_score=persistence,
            payload_score=payload,
            confidence=round(float(min(1.0, confidence)), 4),
            contact_count=rec.contacts,
            observation_secs=round(rec.duration_secs(), 1),
            evidence={
                "raw_periodicity_score": round(periodicity_score, 4),
                "periodicity_signal": p_signal,
                "jitter_ms": round(jitter_ms, 2),
                "persistence_score": persistence,
                "contact_count": rec.contacts,
                "observation_window_secs": round(rec.duration_secs(), 1),
                "payload_score": payload,
                "packet_size_mean": round(packet_size_mean, 2),
                "packet_size_stddev": round(packet_size_stddev, 2),
                "packet_size_cv": round(cv, 4),
                "dst_ip": dst_ip,
            },
        )
