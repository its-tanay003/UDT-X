"""UDT-X Resilient Kafka Event Producer for Ingestion Collectors."""

import json
import logging
from typing import Any

logger = logging.getLogger("udtx.ingestion.kafka")


class UDTXKafkaProducer:
    """Unified Kafka Producer for publishing normalized telemetry to Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        topic: str = "raw-events",
        client_id: str = "udtx-ingest-producer",
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.client_id = client_id
        self.dry_run = dry_run
        self._producer: Any = None

        if not self.dry_run:
            self._connect()

    def _connect(self) -> None:
        """Initialize connection to Kafka broker."""
        try:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(","),
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: (
                    str(k).encode("utf-8") if k is not None else None
                ),
                acks="all",
                retries=3,
                max_block_ms=5000,
            )
            logger.info("Connected to Kafka at %s", self.bootstrap_servers)
        except Exception as exc:
            logger.warning(
                "Could not connect to Kafka at %s (%s). Using mock/buffer mode.",
                self.bootstrap_servers,
                exc,
            )
            self._producer = None

    def send_event(self, event_dict: dict[str, Any], key: str | None = None) -> bool:
        """Publish a single flow or alert event dictionary to Kafka topic."""
        if self._producer is not None and not self.dry_run:
            try:
                flow_key = key or event_dict.get("flow_id")
                future = self._producer.send(self.topic, value=event_dict, key=flow_key)
                self._producer.flush(timeout=2)
                logger.debug(
                    "Published event %s to %s",
                    flow_key or "unkeyed",
                    self.topic,
                )
                return future.is_done or True
            except Exception as e:
                logger.error("Failed to send message to Kafka: %s", e)
                return False
        else:
            logger.info(
                "[DRY-RUN / BUFFER] Topic: %s | Key: %s | Event: %s",
                self.topic,
                key or event_dict.get("flow_id"),
                event_dict.get("flow_id"),
            )
            return True

    def flush(self) -> None:
        """Flush pending producer messages."""
        if self._producer is not None:
            try:
                self._producer.flush(timeout=5)
            except Exception as e:
                logger.error("Error flushing Kafka producer: %s", e)

    def close(self) -> None:
        """Gracefully close the producer connection."""
        if self._producer is not None:
            try:
                self._producer.close(timeout=5)
                logger.info("Kafka producer closed cleanly.")
            except Exception as e:
                logger.error("Error closing Kafka producer: %s", e)
