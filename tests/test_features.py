"""UDT-X Feature Extraction Unit & Synthetic Stream Tests.

Validates:
1. Shannon Entropy against exact theoretical values (0.0, 1.0, 2.0 bits).
2. Autocorrelation Periodicity score on constant, jittered, and Poisson streams.
3. DNS N-gram anomaly score on legitimate vs DGA domains.
4. Directional, temporal, network throughput rate calculations.
5. End-to-end FeatureVector extraction and Pydantic validation.
"""

import math
from datetime import UTC, datetime

from features.extractor import (
    calculate_directional_ratios,
    calculate_iat_and_jitter,
    calculate_ngram_anomaly_score,
    calculate_periodicity_score,
    calculate_shannon_entropy,
    calculate_throughput_rates,
)
from features.window_store import FlowSnapshot, SlidingWindowStore
from features.worker import FeatureExtractionWorker
from schema.models import (
    DNSData,
    FeatureVector,
    FlowDirection,
    FlowEvent,
    FlowSource,
    TLSData,
)


# ==============================================================================
# 1. Shannon Entropy Tests
# ==============================================================================
def test_shannon_entropy_known_theoretical_values() -> None:
    """Verify Shannon entropy calculation against known mathematical ground truth."""
    # Empty & 1-char repeating strings have 0 bits of information
    assert calculate_shannon_entropy("") == 0.0
    assert calculate_shannon_entropy("a") == 0.0
    assert calculate_shannon_entropy("aaaaaaa") == 0.0

    # 2 equal-probability symbols: - 2 * (0.5 * log2(0.5)) = 1.0 bit
    assert math.isclose(calculate_shannon_entropy("ab"), 1.0, rel_tol=1e-3)
    assert math.isclose(calculate_shannon_entropy("aabb"), 1.0, rel_tol=1e-3)

    # 4 equal-probability symbols: - 4 * (0.25 * log2(0.25)) = 2.0 bits
    assert math.isclose(calculate_shannon_entropy("abcd"), 2.0, rel_tol=1e-3)

    # 8 equal-probability symbols: log2(8) = 3.0 bits
    assert math.isclose(calculate_shannon_entropy("abcdefgh"), 3.0, rel_tol=1e-3)


# ==============================================================================
# 2. Autocorrelation & Periodicity Score Tests
# ==============================================================================
def test_periodicity_score_strictly_constant_beacon() -> None:
    """A strictly regular interval sequence (e.g. exactly 10s beacon) must yield 1.0."""
    intervals = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    score = calculate_periodicity_score(intervals)
    assert score == 1.0


def test_periodicity_score_periodic_with_low_jitter() -> None:
    """A regular beacon with realistic network jitter (±2%) should yield > 0.90."""
    intervals = [10.05, 9.95, 10.02, 9.98, 10.01, 10.04, 9.96]
    score = calculate_periodicity_score(intervals)
    assert score >= 0.90


def test_periodicity_score_poisson_random_traffic() -> None:
    """A highly erratic / random Poisson interval sequence should yield < 0.35."""
    intervals = [0.2, 54.8, 2.1, 120.5, 0.4, 76.2, 1.1, 98.4]
    score = calculate_periodicity_score(intervals)
    assert score < 0.35


# ==============================================================================
# 3. DNS N-Gram Anomaly Score Tests
# ==============================================================================
def test_ngram_anomaly_score_legitimate_vs_dga() -> None:
    """Verify natural English domains score low anomaly and DGA strings score high."""
    # Natural domain names containing common English bigrams
    legit_score_google = calculate_ngram_anomaly_score("google.com")
    legit_score_apple = calculate_ngram_anomaly_score("apple.com")
    legit_score_internal = calculate_ngram_anomaly_score("auth-server.corp.local")

    assert legit_score_google < 0.35
    assert legit_score_apple < 0.35
    assert legit_score_internal < 0.35

    # Random consonant-heavy DGA domains
    dga_score_1 = calculate_ngram_anomaly_score("xqzrwpkz7941q.biz")
    dga_score_2 = calculate_ngram_anomaly_score("vbxzqwtykp.cc")

    assert dga_score_1 > 0.70
    assert dga_score_2 > 0.70


# ==============================================================================
# 4. Inter-Arrival Time (IAT) & Throughput Tests
# ==============================================================================
def test_iat_and_jitter_calculation() -> None:
    """Verify IAT and jitter across timestamps."""
    # 4 timestamps spaced exactly 1000ms apart
    timestamps = [1000.0, 2000.0, 3000.0, 4000.0]
    iat, jitter = calculate_iat_and_jitter(timestamps)
    assert iat == 1000.0
    assert jitter == 0.0


def test_throughput_and_directional_ratios() -> None:
    """Verify rate calculations."""
    pps, bps = calculate_throughput_rates(
        byte_count=10000, packet_count=10, duration_ms=2000.0
    )
    assert pps == 5.0
    assert bps == 5000.0

    byte_ratio, pkt_ratio = calculate_directional_ratios(
        outbound_bytes=8000, inbound_bytes=2000, outbound_pkts=8, inbound_pkts=2
    )
    assert byte_ratio == 4.0
    assert pkt_ratio == 4.0


# ==============================================================================
# 5. Sliding Window Store Tests
# ==============================================================================
def test_sliding_window_store_in_memory_eviction() -> None:
    """Verify that entries outside sliding window window_seconds are evicted."""
    store = SlidingWindowStore(window_seconds=10)
    src_ip = "192.168.1.50"

    # Old snapshot (timestamp 0)
    store.add_flow(
        src_ip,
        FlowSnapshot(
            flow_id="f1",
            timestamp_ms=1000.0,
            dst_ip="8.8.8.8",
            dst_port=53,
            protocol="UDP",
            direction="outbound",
            bytes=100,
            packets=1,
        ),
    )

    # New snapshot (timestamp 15000ms, i.e., 15s later)
    store.add_flow(
        src_ip,
        FlowSnapshot(
            flow_id="f2",
            timestamp_ms=15000.0,
            dst_ip="8.8.8.8",
            dst_port=53,
            protocol="UDP",
            direction="outbound",
            bytes=200,
            packets=2,
        ),
    )

    # Window cutoff is 15000 - 10000 = 5000ms -> f1 should be evicted
    active = store.get_window_snapshots(src_ip, current_ts_ms=15000.0)
    assert len(active) == 1
    assert active[0].flow_id == "f2"


# ==============================================================================
# 6. End-to-End FeatureVector Extraction Test
# ==============================================================================
def test_feature_extraction_worker_end_to_end() -> None:
    """Process a stream of synthetic FlowEvents through FeatureExtractionWorker."""
    worker = FeatureExtractionWorker(dry_run=True, window_seconds=60)

    # Create 3 sequential synthetic beacon flows
    flows = [
        FlowEvent(
            flow_id=f"flow-beacon-{i}",
            timestamp=datetime(2026, 8, 26, 12, 0, i * 10, tzinfo=UTC),
            src_ip="10.0.0.15",
            dst_ip="93.184.216.34",
            src_port=49152 + i,
            dst_port=443,
            protocol="TCP",
            direction=FlowDirection.OUTBOUND,
            bytes=500 + (i * 10),
            packets=5,
            duration_ms=100.0,
            tls=TLSData(
                ja3="771,4865-4866-4867,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0",
                sni="c2.threat-actor.org",
            ),
            dns=DNSData(query="c2.threat-actor.org", entropy=3.12),
            source=FlowSource.PCAP,
        )
        for i in range(4)
    ]

    last_fv: FeatureVector | None = None
    for f in flows:
        last_fv = worker.extract_features_from_flow(f)

    assert last_fv is not None
    assert isinstance(last_fv, FeatureVector)
    assert last_fv.src_ip == "10.0.0.15"
    assert last_fv.dst_ip == "93.184.216.34"

    # Network window features
    assert last_fv.network.window_flow_count == 4
    assert last_fv.network.window_unique_dst_ips == 1
    assert last_fv.network.packets_per_sec > 0.0

    # Directional
    assert last_fv.directional.direction == FlowDirection.OUTBOUND
    assert last_fv.directional.outbound_bytes_window > 0

    # Temporal & Periodicity (10s intervals -> high periodicity score)
    assert last_fv.temporal.inter_arrival_time_ms == 10000.0
    assert last_fv.temporal.periodicity_score >= 0.90

    # DNS features
    assert last_fv.dns is not None
    assert last_fv.dns.query == "c2.threat-actor.org"
    assert last_fv.dns.domain_entropy == 3.12
    assert last_fv.dns.dns_query_frequency_window == 4

    # TLS features (zero decrypted payload)
    assert last_fv.tls is not None
    assert last_fv.tls.ja3 is not None
    assert last_fv.tls.sni == "c2.threat-actor.org"

    # Verify JSON Schema validation
    fv_json = last_fv.model_dump_json()
    reloaded = FeatureVector.model_validate_json(fv_json)
    assert reloaded.flow_id == last_fv.flow_id
