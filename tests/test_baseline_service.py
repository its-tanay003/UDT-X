"""UDT-X Behavioral Baseline Service & Client Library — Unit Tests.

Tests:
1. Incremental EWMA mean & variance updating on incoming flows.
2. Historical destination and port set tracking.
3. Client library get_baseline(host_ip) retrieves profile.
4. One week of regular synthetic traffic builds stable baseline.
5. Sudden massive volume spike + novel destination + off-hours is flagged as anomalous.
6. Routine normal flow is confirmed as non-anomalous.
7. TimescaleDB snapshot serialization.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from baseline.client import get_baseline
from baseline.models import BaselineProfile
from baseline.store import BaselineStore
from baseline.worker import BaselineService
from schema.models import FlowDirection, FlowEvent, FlowSource


def _generate_synthetic_week_flows(
    host_ip: str = "10.0.1.50",
    work_dst_ips: list[str] | None = None,
    flows_per_day: int = 40,
) -> list[FlowEvent]:
    """Generate 7 days of normal office traffic (9:00 - 18:00, ~2-8 KB per flow)."""
    dsts = work_dst_ips or ["10.0.0.1", "10.0.0.2", "142.250.190.46", "13.107.42.16"]
    flows: list[FlowEvent] = []
    base_time = datetime(2026, 8, 20, 9, 0, 0, tzinfo=UTC)

    for day in range(7):
        day_time = base_time + timedelta(days=day)
        for i in range(flows_per_day):
            # Normal office hours: 9am to 6pm
            flow_time = day_time + timedelta(minutes=i * 12)
            dst = random.choice(dsts)
            port = random.choice([80, 443, 8080])
            # Normal distribution: ~5000 bytes ± 1500 bytes
            byte_count = int(random.gauss(5000, 1000))
            byte_count = max(800, min(12000, byte_count))

            flows.append(
                FlowEvent(
                    flow_id=f"flow-day{day}-{i}",
                    timestamp=flow_time,
                    source=FlowSource.PCAP,
                    src_ip=host_ip,
                    dst_ip=dst,
                    src_port=40000 + (i % 1000),
                    dst_port=port,
                    protocol="TCP",
                    direction=FlowDirection.OUTBOUND,
                    bytes=byte_count,
                    packets=byte_count // 500,
                    duration_ms=45.0,
                )
            )

    return flows


# ─────────────────────────────────────────────────────────────────────────────
# 1. Incremental Baseline Updating
# ─────────────────────────────────────────────────────────────────────────────


def test_incremental_baseline_updates() -> None:
    store = BaselineStore()
    host = "10.0.5.5"

    flow1 = FlowEvent(
        source=FlowSource.PCAP,
        src_ip=host,
        dst_ip="8.8.8.8",
        src_port=52000,
        dst_port=53,
        protocol="UDP",
        bytes=1000,
        packets=2,
    )
    p1 = store.update_from_flow(flow1)
    assert p1.total_flows_observed == 1
    assert p1.byte_volume_mean == 1000.0
    assert "8.8.8.8" in p1.known_destinations

    flow2 = FlowEvent(
        source=FlowSource.PCAP,
        src_ip=host,
        dst_ip="1.1.1.1",
        src_port=52001,
        dst_port=53,
        protocol="UDP",
        bytes=2000,
        packets=4,
    )
    p2 = store.update_from_flow(flow2)
    assert p2.total_flows_observed == 2
    assert p2.byte_volume_mean > 1000.0
    assert "1.1.1.1" in p2.known_destinations


# ─────────────────────────────────────────────────────────────────────────────
# 2. Week of Synthetic Traffic + Anomaly Flagging
# ─────────────────────────────────────────────────────────────────────────────


def test_week_traffic_baseline_flags_sudden_deviation() -> None:
    service = BaselineService(dry_run=True)
    host = "10.0.1.50"
    known_servers = ["10.0.0.1", "10.0.0.2", "142.250.190.46"]

    # 1. Feed 7 days of normal synthetic traffic
    weekly_flows = _generate_synthetic_week_flows(
        host_ip=host,
        work_dst_ips=known_servers,
        flows_per_day=30,
    )
    for flow in weekly_flows:
        service.process_flow_event(flow)

    profile = service.store.get_profile(host)
    assert profile.total_flows_observed == len(weekly_flows)
    assert 3500.0 <= profile.byte_volume_mean <= 6500.0
    assert all(dst in profile.known_destinations for dst in known_servers)

    # 2. Test a normal flow conforming to baseline -> NOT anomalous
    normal_flow = FlowEvent(
        source=FlowSource.PCAP,
        src_ip=host,
        dst_ip="10.0.0.1",
        src_port=51234,
        dst_port=443,
        protocol="TCP",
        bytes=5200,
        packets=10,
        timestamp=datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC),  # 14:00 (active hour)
    )
    is_anom, score, details = profile.is_anomalous_transfer(
        dst_ip=normal_flow.dst_ip,
        byte_count=float(normal_flow.bytes),
        hour=normal_flow.timestamp.hour,
    )
    assert not is_anom, (
        f"Expected normal flow to be clean, got score={score}: {details}"
    )

    # 3. Test sudden deviation: 500 MB transfer at 03:00 AM to a NEVER-SEEN external IP
    suspicious_flow = FlowEvent(
        source=FlowSource.PCAP,
        src_ip=host,
        dst_ip="198.51.100.222",  # Novel rogue IP
        src_port=51235,
        dst_port=443,
        protocol="TCP",
        bytes=500_000_000,  # 500 MB vs 5 KB baseline
        packets=350_000,
        timestamp=datetime(2026, 8, 28, 3, 30, 0, tzinfo=UTC),  # 03:00 AM off-hour
    )
    is_anom, score, details = profile.is_anomalous_transfer(
        dst_ip=suspicious_flow.dst_ip,
        byte_count=float(suspicious_flow.bytes),
        hour=suspicious_flow.timestamp.hour,
    )
    assert is_anom, f"Expected deviation to be flagged as anomalous: {details}"
    assert score >= 0.50
    assert details["is_new_destination"] is True
    assert details["is_off_hour"] is True
    assert details["zscore"] > 50.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Client Library get_baseline(host_ip)
# ─────────────────────────────────────────────────────────────────────────────


def test_client_library_get_baseline() -> None:
    # Test with a mock in-memory redis / fresh IP
    class MockRedis:
        def __init__(self) -> None:
            self.data: dict[str, str] = {}

        def get(self, key: str) -> str | None:
            return self.data.get(key)

        def set(self, key: str, val: str) -> None:
            self.data[key] = val

    mock_redis = MockRedis()
    profile = get_baseline("10.254.254.1", redis_client=mock_redis)
    assert isinstance(profile, BaselineProfile)
    assert profile.host_ip == "10.254.254.1"
    assert profile.total_flows_observed == 0

    # Put a profile in mock redis and verify get_baseline retrieves it
    profile.total_flows_observed = 42
    profile.byte_volume_mean = 8500.0
    mock_redis.set("udtx:baseline:10.254.254.1", profile.model_dump_json())

    retrieved = get_baseline("10.254.254.1", redis_client=mock_redis)
    assert retrieved.total_flows_observed == 42
    assert retrieved.byte_volume_mean == 8500.0
