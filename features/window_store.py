"""UDT-X Redis & In-Memory Sliding Window Manager.

Maintains stateful sliding window aggregations per host (`src_ip`) and
host-destination pair `(src_ip, dst_ip)` for real-time feature extraction.
"""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger("udtx.features.window_store")


@dataclass
class FlowSnapshot:
    """Compact record retained in sliding time window."""

    flow_id: str
    timestamp_ms: float
    dst_ip: str
    dst_port: int
    protocol: str
    direction: str
    bytes: int
    packets: int
    is_dns: bool = False
    query: str = ""


class SlidingWindowStore:
    """Sliding window store with Redis backend and automatic In-Memory fallback."""

    def __init__(
        self,
        redis_client: Any | None = None,
        redis_url: str | None = None,
        window_seconds: int = 60,
        max_history_entries: int = 100,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_history_entries = max_history_entries
        self.redis = redis_client
        self.redis_url = redis_url
        self._in_memory_store: dict[str, deque[FlowSnapshot]] = defaultdict(deque)

        if self.redis is None and self.redis_url:
            self._connect_redis()

    def _connect_redis(self) -> None:
        """Attempt connection to Redis."""
        try:
            import redis

            self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Connected to Redis sliding window backend.")
        except Exception as exc:
            logger.warning(
                "Redis connection failed (%s); using in-memory window store.",
                exc,
            )
            self.redis = None

    def add_flow(self, src_ip: str, snapshot: FlowSnapshot) -> None:
        """Add a flow event to the sliding window for src_ip."""
        cutoff_ms = snapshot.timestamp_ms - (self.window_seconds * 1000.0)

        # In-Memory storage (always maintained as local cache / fallback)
        q = self._in_memory_store[src_ip]
        q.append(snapshot)
        while q and q[0].timestamp_ms < cutoff_ms:
            q.popleft()
        while len(q) > self.max_history_entries:
            q.popleft()

        # Redis storage
        if self.redis is not None:
            key = f"udtx:win:{src_ip}"
            try:
                payload = json.dumps(asdict(snapshot))
                self.redis.zadd(key, {payload: snapshot.timestamp_ms})
                self.redis.zremrangebyscore(key, "-inf", cutoff_ms)
                # Set TTL on window key
                self.redis.expire(key, self.window_seconds * 2)
            except Exception as e:
                logger.debug("Redis zadd error for %s: %s", src_ip, e)

    def get_window_snapshots(
        self, src_ip: str, current_ts_ms: float | None = None
    ) -> list[FlowSnapshot]:
        """Retrieve all active flow snapshots for src_ip within sliding window."""
        if current_ts_ms is None:
            current_ts_ms = time.time() * 1000.0
        cutoff_ms = current_ts_ms - (self.window_seconds * 1000.0)

        if self.redis is not None:
            key = f"udtx:win:{src_ip}"
            try:
                records = self.redis.zrangebyscore(
                    key, cutoff_ms, "+inf", withscores=False
                )
                snapshots: list[FlowSnapshot] = []
                for rec in records:
                    data = json.loads(rec)
                    snapshots.append(FlowSnapshot(**data))
                if snapshots:
                    return snapshots
            except Exception as e:
                logger.debug("Redis zrange error for %s: %s", src_ip, e)

        # In-Memory fallback
        q = self._in_memory_store.get(src_ip, deque())
        return [s for s in q if s.timestamp_ms >= cutoff_ms]
