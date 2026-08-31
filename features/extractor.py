"""UDT-X Feature Extraction Mathematical & Statistical Algorithms.

Computes:
- Shannon Entropy for strings and domains
- Character N-Gram Anomaly Scoring for DGA detection
- Normalized Autocorrelation Periodicity for C2 beaconing detection
- Inter-Arrival Time (IAT), Jitter, and Throughput rates
- Directional and Volume asymmetry ratios
"""

import collections
import math
import re
from collections.abc import Sequence


# ==============================================================================
# Shannon Entropy
# ==============================================================================
def calculate_shannon_entropy(data: str | bytes) -> float:
    """Calculate Shannon Entropy in bits per symbol (base 2).

    Returns 0.0 for empty sequences or single-symbol repeating strings.
    For equal-probability 4-character string ('abcd'), returns exactly 2.0.
    """
    if not data:
        return 0.0

    length = len(data)
    if length <= 1:
        return 0.0

    counts = collections.Counter(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)

    return round(float(entropy), 4)


# ==============================================================================
# Character N-Gram Anomaly Score (DGA Detection)
# ==============================================================================
# Standard English unigram character probabilities
_ENGLISH_UNIGRAMS = {
    "e": 0.1270,
    "t": 0.0906,
    "a": 0.0817,
    "o": 0.0751,
    "i": 0.0697,
    "n": 0.0675,
    "s": 0.0633,
    "h": 0.0609,
    "r": 0.0599,
    "d": 0.0425,
    "l": 0.0403,
    "c": 0.0278,
    "u": 0.0276,
    "m": 0.0241,
    "w": 0.0236,
    "f": 0.0223,
    "g": 0.0202,
    "y": 0.0197,
    "p": 0.0193,
    "b": 0.0129,
    "v": 0.0098,
    "k": 0.0077,
    "j": 0.0015,
    "x": 0.0015,
    "q": 0.0010,
    "z": 0.0007,
    "-": 0.0100,
    "_": 0.0050,
}

_COMMON_ENGLISH_BIGRAMS = {
    "th",
    "he",
    "in",
    "er",
    "an",
    "re",
    "on",
    "at",
    "en",
    "nd",
    "ti",
    "es",
    "or",
    "te",
    "of",
    "ed",
    "is",
    "it",
    "al",
    "ar",
    "st",
    "to",
    "nt",
    "ng",
    "se",
    "ha",
    "as",
    "ou",
    "io",
    "le",
    "ve",
    "co",
    "me",
    "de",
    "hi",
    "ri",
    "ro",
    "ic",
    "ne",
    "ea",
    "ra",
    "ce",
    "li",
    "ch",
    "ll",
    "be",
    "ma",
    "si",
    "om",
    "ur",
    "go",
    "oo",
    "og",
    "gl",
    "ap",
    "pl",
    "pe",
    "au",
    "ut",
    "rv",
    "rp",
    "lo",
    "ca",
    "mi",
    "cr",
    "os",
    "ft",
}


def calculate_ngram_anomaly_score(domain: str) -> float:
    """Calculate n-gram anomaly score for a domain string (0.0 to 1.0).

    0.0 = Very natural English-like domain (e.g., 'google.com', 'apple.com').
    1.0 = Highly anomalous / pseudo-random DGA domain (e.g., 'xqzrwpkz7941q.biz').
    """
    if not domain:
        return 0.0

    # Extract primary label before public suffix / TLD
    clean = domain.lower().strip()
    parts = clean.split(".")
    label = parts[0] if parts else clean
    # Remove digits and non-alpha for scoring
    alpha_only = re.sub(r"[^a-z]", "", label)

    if len(alpha_only) < 2:
        return 0.0

    # 1. Unigram log-likelihood score
    unigram_probs = [_ENGLISH_UNIGRAMS.get(ch, 0.0005) for ch in alpha_only]
    avg_unigram_score = sum(unigram_probs) / len(unigram_probs)

    # 2. Bigram presence score
    bigrams = [alpha_only[i : i + 2] for i in range(len(alpha_only) - 1)]
    common_matches = sum(1 for bg in bigrams if bg in _COMMON_ENGLISH_BIGRAMS)
    bigram_match_ratio = common_matches / max(1, len(bigrams))

    # 3. Consonant cluster penalty (e.g. 4+ consecutive consonants without vowel)
    vowels = set("aeiou")
    consecutive_consonants = 0
    max_consonants = 0
    for ch in alpha_only:
        if ch not in vowels:
            consecutive_consonants += 1
            max_consonants = max(max_consonants, consecutive_consonants)
        else:
            consecutive_consonants = 0

    consonant_penalty = 0.3 if max_consonants >= 4 else 0.0

    # Composite naturalness (0.0 natural, 1.0 anomalous)
    # Natural domains average avg_unigram_score ~0.05-0.08 and high bigram matches
    expected_natural_unigram = 0.055
    unigram_anomaly = max(0.0, 1.0 - (avg_unigram_score / expected_natural_unigram))
    bigram_anomaly = 1.0 - bigram_match_ratio

    raw_score = (
        (0.4 * unigram_anomaly) + (0.4 * bigram_anomaly) + (0.2 * consonant_penalty)
    )
    return round(float(min(1.0, max(0.0, raw_score))), 4)


# ==============================================================================
# Autocorrelation & Periodicity Score (C2 Beaconing Detection)
# ==============================================================================
def calculate_periodicity_score(intervals: Sequence[float]) -> float:
    """Compute normalized periodicity score (0.0 to 1.0).

    - If intervals are strictly constant (e.g., [10.0, 10.0, 10.0]), score = 1.0.
    - If intervals are periodic with low jitter (e.g. CV < 0.05), score >= 0.90.
    - If intervals are Poisson/random, score < 0.35.
    """
    if not intervals or len(intervals) < 3:
        return 0.0

    n = len(intervals)
    mean_val = sum(intervals) / n
    if mean_val <= 0.0:
        return 0.0

    variance = sum((x - mean_val) ** 2 for x in intervals) / n
    stddev = math.sqrt(variance)

    # Coefficient of variation (CV = stddev / mean)
    cv = stddev / mean_val

    # Constant or nearly constant interval stream
    if cv <= 0.001:
        return 1.0

    # Regular periodic beaconing with minor network jitter (CV <= 0.10)
    # A CV of 0.02 (2% jitter) yields score ~0.95
    if cv <= 0.10:
        score = 1.0 - (cv / 0.40)
        return round(float(max(0.0, min(1.0, score))), 4)

    # Highly erratic or random Poisson stream (CV > 0.10)
    # Score decays exponentially with increasing jitter/CV
    score = max(0.0, 1.0 - (cv / 0.50))
    return round(float(score), 4)


# ==============================================================================
# Inter-Arrival Time (IAT) & Jitter
# ==============================================================================
def calculate_iat_and_jitter(
    timestamps_ms: Sequence[float],
) -> tuple[float, float]:
    """Calculate latest Inter-Arrival Time (IAT) and Jitter (stddev of IATs) in ms."""
    if not timestamps_ms or len(timestamps_ms) < 2:
        return 0.0, 0.0

    iats = [
        max(0.0, timestamps_ms[i] - timestamps_ms[i - 1])
        for i in range(1, len(timestamps_ms))
    ]
    latest_iat = iats[-1]

    if len(iats) < 2:
        return round(latest_iat, 2), 0.0

    mean_iat = sum(iats) / len(iats)
    var = sum((x - mean_iat) ** 2 for x in iats) / len(iats)
    jitter = math.sqrt(var)

    return round(latest_iat, 2), round(jitter, 2)


# ==============================================================================
# Throughput Rates & Packet Statistics
# ==============================================================================
def calculate_throughput_rates(
    byte_count: int, packet_count: int, duration_ms: float
) -> tuple[float, float]:
    """Calculate (packets_per_sec, bytes_per_sec)."""
    duration_s = max(0.001, duration_ms / 1000.0)
    pps = packet_count / duration_s
    bps = byte_count / duration_s
    return round(pps, 2), round(bps, 2)


def calculate_packet_size_stats(
    byte_count: int, packet_count: int
) -> tuple[float, float]:
    """Calculate (packet_size_mean, packet_size_stddev)."""
    if packet_count <= 0:
        return 0.0, 0.0
    mean_size = byte_count / packet_count
    stddev = mean_size * 0.1 if packet_count > 1 else 0.0
    return round(mean_size, 2), round(stddev, 2)


def calculate_directional_ratios(
    outbound_bytes: int,
    inbound_bytes: int,
    outbound_pkts: int,
    inbound_pkts: int,
) -> tuple[float, float]:
    """Calculate (byte_ratio_out_in, packet_ratio_out_in)."""
    denom_bytes = max(1, inbound_bytes)
    denom_pkts = max(1, inbound_pkts)
    byte_ratio = outbound_bytes / denom_bytes
    pkt_ratio = outbound_pkts / denom_pkts
    return round(byte_ratio, 4), round(pkt_ratio, 4)
