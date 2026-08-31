"""UDT-X Threat Intelligence Streaming Worker.

Consumes raw-alerts, enriches with MITRE techniques & local IOC indicators,
and publishes canonical enriched records to `enriched-alerts`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ingestion.kafka_producer import UDTXKafkaProducer
from intel.enricher import ThreatIntelEnricher
from schema.models import Alert

logger = logging.getLogger("udtx.intel.worker")


class IntelEnrichmentService:
    """Kafka streaming service for MITRE ATT&CK & IOC threat intel enrichment."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "raw-alerts",
        output_topic: str = "enriched-alerts",
        group_id: str = "udtx-intel-enrichment-service",
        mitre_map_path: str | Path = "intel/mitre_map.json",
        ioc_feed_path: str | Path | None = "intel/data/sample_iocs.json",
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.dry_run = dry_run

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            client_id="udtx-intel-producer",
            dry_run=dry_run,
        )

        self.enricher = ThreatIntelEnricher(
            mitre_map_path=mitre_map_path,
            ioc_feed_path=ioc_feed_path,
        )

    def process_alert(self, alert: Alert) -> Alert:
        """Enrich Alert and emit to enriched-alerts topic."""
        enriched = self.enricher.enrich_alert(alert)

        # Publish to Kafka
        self.producer.send_event(
            event_dict=enriched.model_dump(mode="json"),
            key=enriched.src_ip,
        )

        logger.info(
            "Enriched Alert %s (%s) with %d MITRE techniques and %d evidence items",
            enriched.alert_id,
            enriched.threat_class,
            len(enriched.mitre),
            len(enriched.evidence),
        )
        return enriched

    def process_raw_message(self, msg_val: Any) -> Alert | None:
        try:
            if isinstance(msg_val, (bytes, bytearray)):
                data = json.loads(msg_val.decode("utf-8"))
            elif isinstance(msg_val, str):
                data = json.loads(msg_val)
            else:
                data = msg_val
            alert = Alert.model_validate(data)
            return self.process_alert(alert)
        except Exception as exc:
            logger.warning("Failed to process message for intel enrichment: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Intel Enrichment Service running in dry-run mode.")
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
            logger.info("Intel Enrichment Service subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Intel Enrichment Service consumer error: %s", exc)
