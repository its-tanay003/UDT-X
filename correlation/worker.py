"""UDT-X Correlation Streaming Service Worker.

Consumes raw-alerts, writes graph nodes to Neo4j, groups alerts into Incidents,
and publishes enriched incidents to `correlated-incidents`.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from correlation.correlator import IncidentCorrelator
from correlation.graph_client import Neo4jEvidenceGraph
from correlation.models import Incident
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import Alert

logger = logging.getLogger("udtx.correlation.worker")


class CorrelationService:
    """Streaming Correlation & Graph Service consuming raw-alerts."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "raw-alerts",
        output_topic: str = "correlated-incidents",
        group_id: str = "udtx-correlation-service",
        neo4j_uri: str | None = None,
        window_minutes: int = 30,
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
            client_id="udtx-correlation-producer",
            dry_run=dry_run,
        )

        self.graph = Neo4jEvidenceGraph(uri=neo4j_uri, dry_run=dry_run)
        self.correlator = IncidentCorrelator(window_minutes=window_minutes)

    def process_alert(self, alert: Alert) -> Incident:
        """Process an Alert: write to Neo4j, correlate into Incident, and publish."""
        # 1. Write Alert node to Neo4j
        self.graph.write_alert_node(alert)

        # 2. Correlate into Incident
        incident, is_new = self.correlator.correlate_alert(alert)

        # 3. Write/Update Incident in Neo4j
        self.graph.write_incident_node(incident)

        # 4. Emit to correlated-incidents Kafka topic
        self.producer.send_event(
            event_dict=incident.model_dump(mode="json"),
            key=incident.primary_host_ip,
        )

        logger.info(
            "Correlated Alert %s into Incident %s (Status: %s, Chain: %s, Alerts: %d)",
            alert.alert_id,
            incident.incident_id,
            incident.status.value,
            incident.attack_chain.value if incident.attack_chain else "None",
            len(incident.alert_ids),
        )
        return incident

    def process_raw_message(self, msg_val: Any) -> Incident | None:
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
            logger.warning("Correlation service failed to process message: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Correlation Service running in dry-run mode.")
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
            logger.info("Correlation Service subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Correlation Service consumer error: %s", exc)
