"""UDT-X Streaming Flow Normalizer Worker Loop."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from ingestion.kafka_producer import UDTXKafkaProducer
from normalizer.transformer import transform_to_flow_event

logger = logging.getLogger("udtx.normalizer.worker")


class FlowNormalizerWorker:
    """Consumes raw-events, validates & normalizes FlowEvents, routes errors to DLQ."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "raw-events",
        output_topic: str = "flow-events",
        dlq_topic: str = "raw-events-dlq",
        group_id: str = "udtx-flow-normalizer-group",
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.dlq_topic = dlq_topic
        self.group_id = group_id
        self.dry_run = dry_run

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            topic=self.output_topic,
            client_id="udtx-normalizer-producer",
            dry_run=self.dry_run,
        )

        self.dlq_producer = UDTXKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            topic=self.dlq_topic,
            client_id="udtx-normalizer-dlq",
            dry_run=self.dry_run,
        )

        self.processed_count = 0
        self.success_count = 0
        self.dlq_count = 0

    def process_record(self, raw_message: Any) -> bool:
        """Process a single raw message dict or string.

        Returns True if successfully normalized and published, False if sent to DLQ.
        """
        self.processed_count += 1
        raw_dict: Any = raw_message

        # Deserialize if raw string/bytes
        if isinstance(raw_message, (str, bytes)):
            try:
                raw_dict = json.loads(raw_message)
            except Exception as exc:
                self._send_to_dlq(
                    raw_message=str(raw_message),
                    error_type="JSONDecodeError",
                    error_msg=str(exc),
                )
                return False

        try:
            flow_event = transform_to_flow_event(raw_dict)
            event_payload = flow_event.model_dump(mode="json")

            # Publish to canonical flow-events topic
            self.producer.send_event(event_payload, key=flow_event.flow_id)
            self.success_count += 1
            logger.debug("Normalized flow %s successfully", flow_event.flow_id)
            return True

        except Exception as exc:
            logger.warning("Normalization error on record: %s", exc)
            self._send_to_dlq(
                raw_message=raw_dict,
                error_type=type(exc).__name__,
                error_msg=str(exc),
            )
            return False

    def _send_to_dlq(self, raw_message: Any, error_type: str, error_msg: str) -> None:
        """Construct dead-letter queue diagnostic envelope and publish to DLQ."""
        self.dlq_count += 1
        dlq_envelope = {
            "failed_at": datetime.now(UTC).isoformat(),
            "error_type": error_type,
            "error_message": error_msg,
            "source_topic": self.input_topic,
            "original_payload": raw_message,
        }
        self.dlq_producer.send_event(dlq_envelope)
        logger.error("Record routed to DLQ [%s]: %s", self.dlq_topic, error_msg)

    def run_consumer_loop(self) -> None:
        """Continuous consumer loop polling Kafka raw-events topic."""
        from kafka import KafkaConsumer

        logger.info(
            "Connecting Kafka consumer to %s on topic %s...",
            self.bootstrap_servers,
            self.input_topic,
        )

        consumer = KafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.bootstrap_servers.split(","),
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        logger.info("Normalizer worker active and consuming...")
        try:
            for message in consumer:
                self.process_record(message.value)
                if self.processed_count % 1000 == 0:
                    logger.info(
                        "Stats: %d processed | %d normalized | %d DLQ",
                        self.processed_count,
                        self.success_count,
                        self.dlq_count,
                    )
        except KeyboardInterrupt:
            logger.info("Normalizer consumer stopping...")
        finally:
            consumer.close()
            self.producer.close()
            self.dlq_producer.close()
