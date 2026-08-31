"""UDT-X DGA & DNS Tunnelling Detection Engine — Signal Algorithms.

Implements detection and differentiation for:
1. Domain Generation Algorithms (DGA):
   - High Shannon entropy of the domain / label.
   - High n-gram anomaly score (unnatural character sequences, consonant clusters).
   - Random-looking SLD (second-level domain) with short TTL / high frequency.
2. DNS Tunnelling (Data Exfiltration / Infiltration):
   - Very long query strings or subdomains (> 45-60 chars).
   - High unique subdomain count under the same apex domain.
   - High query frequency / volume from a single source host.
   - Encoded payload characteristics (e.g., base32/base64/hex alphabet entropy).

Produces classification as threat_class="DGA" or "DNS_TUNNELING".
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────────────
# Character & Shannon Entropy Helpers
# ─────────────────────────────────────────────────────────────────────────────


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy for string in bits per char."""
    if not text:
        return 0.0
    freq: dict[str, int] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    entropy = 0.0
    length = len(text)
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(float(entropy), 4)


def extract_domain_parts(domain: str) -> tuple[str, str, str]:
    """Split domain into (subdomain, sld, tld).

    Example:
      'a1b2c3d4e5.tunnel.example.com' -> ('a1b2c3d4e5.tunnel', 'example', 'com')
      'xqzrwpkz7941q.biz' -> ('', 'xqzrwpkz7941q', 'biz')
    """
    clean = domain.lower().strip().rstrip(".")
    if not clean:
        return "", "", ""
    parts = clean.split(".")
    if len(parts) == 1:
        return "", parts[0], ""
    if len(parts) == 2:
        return "", parts[0], parts[1]

    tld = parts[-1]
    sld = parts[-2]
    subdomain = ".".join(parts[:-2])
    return subdomain, sld, tld


# ─────────────────────────────────────────────────────────────────────────────
# Host & Apex Domain State Tracker
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class _ApexDomainTracker:
    query_count: int = 0
    unique_subdomains: set[str] = field(default_factory=set)
    total_query_length: int = 0
    max_query_length: int = 0

    def add_query(self, subdomain: str, full_query: str) -> None:
        self.query_count += 1
        if subdomain:
            self.unique_subdomains.add(subdomain)
        q_len = len(full_query)
        self.total_query_length += q_len
        self.max_query_length = max(self.max_query_length, q_len)


# ─────────────────────────────────────────────────────────────────────────────
# Detection Signals & Detector
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class DNSSignals:
    threat_class: str = "NONE"  # "DGA", "DNS_TUNNELING", or "NONE"
    entropy_score: float = 0.0
    ngram_score: float = 0.0
    length_score: float = 0.0
    tunnel_subdomain_score: float = 0.0
    confidence: float = 0.0
    evidence: dict = field(default_factory=dict)


class DGADNSTunnelDetector:
    """Stateful DGA and DNS Tunnelling Detector."""

    # Thresholds
    DGA_ENTROPY_THRESHOLD = 3.4  # bits/char for SLD
    TUNNEL_QUERY_LEN_HIGH = 55  # chars
    TUNNEL_QUERY_LEN_LOW = 35
    TUNNEL_SUBDOMAINS_HIGH = 10  # unique subdomains per apex

    def __init__(self) -> None:
        # Key: (src_ip, apex_domain) -> _ApexDomainTracker
        self._trackers: dict[tuple[str, str], _ApexDomainTracker] = {}

    def _get_tracker(self, src_ip: str, apex_domain: str) -> _ApexDomainTracker:
        key = (src_ip, apex_domain)
        if key not in self._trackers:
            self._trackers[key] = _ApexDomainTracker()
        return self._trackers[key]

    def evaluate(
        self,
        src_ip: str,
        query: str,
        domain_entropy: float | None = None,
        ngram_score: float | None = None,
        query_length: int | None = None,
        query_frequency: int | None = None,
    ) -> DNSSignals:
        if not query:
            return DNSSignals()

        clean_query = query.lower().strip().rstrip(".")
        subdomain, sld, tld = extract_domain_parts(clean_query)
        apex = f"{sld}.{tld}" if sld and tld else clean_query

        # Fallback calculations if features were omitted in the vector
        q_len = query_length if query_length is not None else len(clean_query)
        q_entropy = (
            domain_entropy
            if domain_entropy is not None
            else calculate_entropy(sld or clean_query)
        )

        # Subdomain / Query Length Analysis for Tunnelling
        subdomain_entropy = calculate_entropy(subdomain) if subdomain else 0.0

        tracker = self._get_tracker(src_ip, apex)
        tracker.add_query(subdomain, clean_query)

        # ── 1. Tunnelling Signals ───────────────────────────────────────────
        # Criteria:
        # a) Long query length (> 35-55 chars)
        # b) High unique subdomain fan-out under the same apex (exfil chunking)
        # c) High subdomain entropy (encoded hex/base32/base64 payload)
        len_score = 0.0
        if q_len >= self.TUNNEL_QUERY_LEN_HIGH:
            len_score = 1.0
        elif q_len > self.TUNNEL_QUERY_LEN_LOW:
            len_score = (q_len - self.TUNNEL_QUERY_LEN_LOW) / (
                self.TUNNEL_QUERY_LEN_HIGH - self.TUNNEL_QUERY_LEN_LOW
            )

        unique_sub_count = len(tracker.unique_subdomains)
        subdomain_score = min(1.0, unique_sub_count / self.TUNNEL_SUBDOMAINS_HIGH)

        # Hex/base32 chunk detection in subdomain (e.g. 16+ hex or base32 chars)
        is_encoded_chunk = bool(
            re.search(r"[0-9a-f]{16,}", subdomain)
            or (len(subdomain) > 20 and subdomain_entropy > 3.2)
        )
        encoded_bonus = 0.3 if is_encoded_chunk else 0.0

        tunnel_confidence = min(
            1.0,
            (0.40 * len_score)
            + (0.35 * subdomain_score)
            + (0.25 * (subdomain_entropy / 4.5))
            + encoded_bonus,
        )

        # ── 2. DGA Signals ──────────────────────────────────────────────────
        # Criteria:
        # a) High n-gram anomaly score (unnatural unigrams/bigrams, consonants)
        # b) High SLD Shannon entropy (> 3.3-3.8)
        # c) Minimal / no subdomain (DGA domains are typically sld.tld)
        ng_score = ngram_score if ngram_score is not None else 0.0
        entropy_ratio = min(1.0, max(0.0, (q_entropy - 2.8) / (4.2 - 2.8)))

        # DGA confidence calculation
        dga_confidence = min(
            1.0,
            (0.55 * ng_score) + (0.45 * entropy_ratio),
        )

        # ── 3. Decision & Classification ────────────────────────────────────
        # DGA vs DNS_TUNNELING discrimination:
        # Tunneling: long subdomains / data exfiltration payloads.
        # DGA: random second-level domains without extensive tunneling structure.

        threat_class = "NONE"
        final_confidence = 0.0

        is_tunnel = tunnel_confidence >= 0.50 and (
            len(subdomain) >= 20 or unique_sub_count >= 5
        )
        if is_tunnel:
            threat_class = "DNS_TUNNELING"
            final_confidence = tunnel_confidence
        elif dga_confidence >= 0.50:
            threat_class = "DGA"
            final_confidence = dga_confidence

        return DNSSignals(
            threat_class=threat_class,
            entropy_score=q_entropy,
            ngram_score=ng_score,
            length_score=len_score,
            tunnel_subdomain_score=subdomain_score,
            confidence=round(final_confidence, 4),
            evidence={
                "query": clean_query,
                "domain_entropy": q_entropy,
                "ngram_score": ng_score,
                "query_length": q_len,
                "subdomain": subdomain,
                "subdomain_entropy": subdomain_entropy,
                "unique_subdomains_count": unique_sub_count,
                "apex_domain": apex,
                "query_frequency": query_frequency or tracker.query_count,
                "tunnel_confidence": round(tunnel_confidence, 4),
                "dga_confidence": round(dga_confidence, 4),
            },
        )
