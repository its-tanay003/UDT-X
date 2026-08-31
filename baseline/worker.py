"""UDT-X Behavioral Baseline Service Worker.

Consumes normalized FlowEvent records from `flow-events`, incrementally updates
rolling host baseline profiles in Redis, and periodically triggers audit snapshots.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from baseline.models import BaselineProfile
from baseline.snapshot import TimescaleSnapshotter
from baseline.store import BaselineStore
from schema.models import FlowEvent

logger = logging.getLogger("udtx.baseline.worker")


class BaselineService:
    """Streaming Behavioral Baseline Worker consuming flow-events."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "flow-events",
        group_id: str = "udtx-baseline-service",
        redis_client: Any | None = None,
        database_url: str | None = None,
        snapshot_interval_secs: float = 60.0,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.group_id = group_id
        self.snapshot_interval = snapshot_interval_secs
        self.dry_run = dry_run

        self.store = BaselineStore(redis_client=redis_client)
        self.snapshotter = TimescaleSnapshotter(db_url=database_url)
        self.snapshotter.init_table()

        self.last_snapshot_time = time.monotonic()
        self.flows_processed: int = 0

    def process_flow_event(self, flow: FlowEvent) -> BaselineProfile:
        """Process a single FlowEvent and update baseline."""
        self.flows_processed += 1
        profile = self.store.update_from_flow(flow)

        # Check periodic snapshot trigger
        now = time.monotonic()
        if now - self.last_snapshot_time >= self.snapshot_interval:
            self._do_snapshot()
            self.last_snapshot_time = now

        return profile

    def _do_snapshot(self) -> None:
        profiles = self.store.all_profiles()
        count = self.snapshotter.snapshot_profiles(profiles)
        logger.info("Snapshotted %d baseline profiles to TimescaleDB", count)

    def process_raw_message(self, msg_val: Any) -> BaselineProfile | None:
        try:
            if isinstance(msg_val, (bytes, bytearray)):
                data = json.loads(msg_val.decode("utf-8"))
            elif isinstance(msg_val, str):
                data = json.loads(msg_val)
            else:
                data = msg_val
            flow = FlowEvent.model_validate(data)
            return self.process_flow_event(flow)
        except Exception as exc:
            logger.warning("Baseline service failed to process message: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Baseline service running in dry-run mode.")
            return
        try:
            from kafka import KafkaConsumer  # type: ignore

            consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            logger.info("Baseline Service subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Baseline service consumer error: %s", exc)
        finally:
            self._do_snapshot()
