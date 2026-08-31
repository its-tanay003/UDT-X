"""UDT-X Encrypted-Session Anomaly Detection Engine — Signal Algorithms.

Inspects encrypted session metadata (TLS/QUIC) without payload decryption:
1. JA3 / JA3S Anomaly:
   - Maintains a per-host historical baseline of seen JA3/JA3S fingerprints.
   - Detects unseen/rare or malformed fingerprints (e.g. Cobalt Strike).
   - Frequency / baseline rarity scoring.
2. Packet-Size Sequence Dynamics:
   - Standard browser TLS handshakes have a characteristic ClientHello ->
     ServerHello/Cert -> KeyExchange size profile.
   - Malformed/atypical sequences (e.g., constant packet sizes).
3. Handshake Timing Anomalies:
   - Abnormally slow or instantaneous handshakes.

Composite confidence score triggers Alert with threat_class="ENCRYPTED_ANOMALY".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Common known-good client JA3 fingerprints (standard browsers/tools)
_COMMON_KNOWN_JA3 = {
    # Chrome on Windows / Mac / Linux
    "b32309a26951912be7dba376398abc3b",
    "cd08e31494f9531f560d64c695473da9",
    "72a589da586844d7f0818ce684948eea",
    # Firefox
    "83eb07034a60c559747500029f4081a9",
    "e2de529c91a355debebe4ff421a179fa",
    # Safari
    "2d1033108c909e46a7572714c62c2f6d",
    # Python requests / curl (standard dev tools)
    "0cce74b019b7dd250260e3f9379b9147",
    "4858b99d634288d672ea5317fb4d39f7",
}

# Known malicious or suspicious JA3 fingerprints (Cobalt Strike, Trickbot, Emotet, etc.)
_KNOWN_MALICIOUS_JA3 = {
    "a0e9f5d64349fb13191bc781f81f42e1",  # Cobalt Strike default
    "6734f37431670b3ab4292b8f60f29984",  # Trickbot
    "4d7a28d6f22da2d4030e63f41a45f902",  # Emotet
    "7204f0556f8f7481d454641c888d3f11",  # Metasploit
}


# ─────────────────────────────────────────────────────────────────────────────
# Host TLS Profile Tracker
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class _HostTLSProfile:
    seen_ja3: dict[str, int] = field(default_factory=dict)
    seen_ja3s: dict[str, int] = field(default_factory=dict)
    total_sessions: int = 0

    def record_session(self, ja3: str | None, ja3s: str | None) -> None:
        self.total_sessions += 1
        if ja3:
            self.seen_ja3[ja3] = self.seen_ja3.get(ja3, 0) + 1
        if ja3s:
            self.seen_ja3s[ja3s] = self.seen_ja3s.get(ja3s, 0) + 1

    def ja3_rarity_score(self, ja3: str) -> float:
        """Score from 0.0 (frequent/established) to 1.0 (novel/rare)."""
        if not ja3 or self.total_sessions < 5:
            return 0.0  # Warmup period
        count = self.seen_ja3.get(ja3, 0)
        ratio = count / self.total_sessions
        # If seen in less than 5% of host sessions, considered rare
        if ratio < 0.05:
            return 0.8
        if ratio < 0.20:
            return 0.4
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Encrypted Session Signals & Detector
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class EncryptedSessionSignals:
    ja3_anomaly_score: float = 0.0
    packet_sequence_anomaly_score: float = 0.0
    timing_anomaly_score: float = 0.0
    confidence: float = 0.0
    is_anomaly: bool = False
    evidence: dict = field(default_factory=dict)


class EncryptedSessionDetector:
    """Stateful TLS / QUIC Encrypted Session Anomaly Detector."""

    W_JA3 = 0.50
    W_SEQUENCE = 0.30
    W_TIMING = 0.20

    def __init__(self) -> None:
        self._profiles: dict[str, _HostTLSProfile] = {}

    def _get_profile(self, src_ip: str) -> _HostTLSProfile:
        if src_ip not in self._profiles:
            self._profiles[src_ip] = _HostTLSProfile()
        return self._profiles[src_ip]

    def _evaluate_ja3(
        self,
        src_ip: str,
        ja3: str | None,
        ja3s: str | None,
    ) -> tuple[float, bool, str]:
        """Evaluate JA3 fingerprint validity, known bad status, and host rarity."""
        if not ja3:
            return 0.0, False, "No JA3 provided"

        clean_ja3 = ja3.strip().lower()

        # 1. Known malicious fingerprint match -> immediate maximum score
        if clean_ja3 in _KNOWN_MALICIOUS_JA3:
            return 1.0, True, f"Known malicious JA3 match ({clean_ja3})"

        # 2. Malformed JA3 (must be 32-char hex MD5)
        if not re.fullmatch(r"[0-9a-f]{32}", clean_ja3):
            return 0.9, True, f"Malformed JA3 fingerprint format: {clean_ja3}"

        # 3. Known common browser/client fingerprint -> 0 anomaly
        if clean_ja3 in _COMMON_KNOWN_JA3:
            return 0.0, False, "Known standard client JA3"

        # 4. Profile-based historical rarity
        profile = self._get_profile(src_ip)
        rarity = profile.ja3_rarity_score(clean_ja3)
        return rarity, rarity >= 0.5, "Uncommon/novel JA3 for host profile"

    def _evaluate_packet_sequence(
        self,
        packet_sizes: list[int] | None,
    ) -> tuple[float, str]:
        """Evaluate early packet size sequence in handshake."""
        if not packet_sizes or len(packet_sizes) < 3:
            return 0.0, "Insufficient packet sequence data"

        # Normal TLS handshake sequences start with ClientHello (~200-550B),
        # ServerHello/Cert (~1000-3000B), followed by key exchanges and data.
        # Anomalies:
        # a) All identical packet sizes (e.g. constant padding beacon)
        if len(set(packet_sizes[:5])) == 1:
            return 0.85, "Uniform fixed-size packet sequence in handshake"

        # b) Abnormally tiny packets (< 40 bytes) during TLS handshake
        if any(size < 40 for size in packet_sizes[:3]):
            return 0.70, "Unusually small packet frames (<40B) in TLS handshake"

        return 0.0, "Standard handshake size dynamics"

    def _evaluate_timing(
        self,
        handshake_duration_ms: float | None,
    ) -> tuple[float, str]:
        """Check for handshake duration anomalies."""
        if handshake_duration_ms is None or handshake_duration_ms <= 0.0:
            return 0.0, "Timing data absent"

        # Standard TLS handshake across Internet: 20ms to 800ms
        # Anomaly: Extremely long (> 5000ms) indicating slowloris/stalling,
        # or abnormally instantaneous (0.01ms) on external IP.
        if handshake_duration_ms > 5000.0:
            return (
                0.75,
                f"Abnormally delayed TLS handshake ({handshake_duration_ms:.1f}ms)",
            )
        if handshake_duration_ms < 0.1:
            return (
                0.60,
                f"Suspicious zero-latency handshake ({handshake_duration_ms:.2f}ms)",
            )

        return 0.0, "Normal handshake timing"

    def evaluate(
        self,
        src_ip: str,
        ja3: str | None,
        ja3s: str | None,
        sni: str | None,
        cipher: str | int | None,
        packet_size_sequence: list[int] | None,
        handshake_duration_ms: float | None,
    ) -> EncryptedSessionSignals:
        ja3_score, ja3_flag, ja3_reason = self._evaluate_ja3(src_ip, ja3, ja3s)
        seq_score, seq_reason = self._evaluate_packet_sequence(packet_size_sequence)
        time_score, time_reason = self._evaluate_timing(handshake_duration_ms)

        # Update historical host baseline
        profile = self._get_profile(src_ip)
        profile.record_session(ja3, ja3s)

        # Composite confidence calculation
        confidence = (
            (self.W_JA3 * ja3_score)
            + (self.W_SEQUENCE * seq_score)
            + (self.W_TIMING * time_score)
        )

        is_anomaly = (
            confidence >= 0.45
            or ja3_score >= 0.85
            or seq_score >= 0.80
            or time_score >= 0.70
        )

        return EncryptedSessionSignals(
            ja3_anomaly_score=ja3_score,
            packet_sequence_anomaly_score=seq_score,
            timing_anomaly_score=time_score,
            confidence=round(float(min(1.0, confidence)), 4),
            is_anomaly=is_anomaly,
            evidence={
                "ja3": ja3,
                "ja3s": ja3s,
                "sni": sni,
                "cipher": cipher,
                "ja3_anomaly_score": ja3_score,
                "ja3_reason": ja3_reason,
                "packet_sequence": packet_size_sequence or [],
                "packet_sequence_anomaly_score": seq_score,
                "packet_sequence_reason": seq_reason,
                "handshake_duration_ms": handshake_duration_ms,
                "timing_anomaly_score": time_score,
                "timing_reason": time_reason,
                "host_total_sessions": profile.total_sessions,
            },
        )
