"""UDT-X Risk Engine Streaming Service (Phase 10).

Consumes enriched-alerts and correlated-incidents, computes multidimensional
risk_scores, registers asset criticality, updates alert store, and republishes
fully scored records to `alerts`.
"""

from __future__ import annotations

import logging

from alert_manager.store import AlertManagerStore, global_alert_store
from correlation.models import Incident
from ingestion.kafka_producer import UDTXKafkaProducer
from risk_engine.calculator import AssetCriticalityRegistry, RiskEngineCalculator
from schema.models import Alert

logger = logging.getLogger("udtx.risk_engine.worker")


class RiskEngineService:
    """Kafka streaming service for Risk Scoring & Incident Management."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        enriched_alerts_topic: str = "enriched-alerts",
        incidents_topic: str = "correlated-incidents",
        output_topic: str = "alerts",
        group_id: str = "udtx-risk-engine-service",
        store: AlertManagerStore | None = None,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.enriched_alerts_topic = enriched_alerts_topic
        self.incidents_topic = incidents_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.dry_run = dry_run

        self.store = store or global_alert_store
        self.calculator = RiskEngineCalculator(AssetCriticalityRegistry())

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            client_id="udtx-risk-engine-producer",
            dry_run=dry_run,
        )

    def process_alert(self, alert: Alert) -> Alert:
        """Score alert, persist in store, and emit to output topic."""
        final_risk = self.calculator.calculate_alert_risk(alert)
        alert.risk_score = final_risk

        # Persist in Alert Manager
        self.store.save_alert(alert)

        # Publish to downstream SOC topic
        self.producer.send_event(
            event_dict=alert.model_dump(mode="json"),
            key=alert.src_ip,
        )

        logger.info(
            "Scored Alert %s: [Threat: %s, Confidence: %.2f, Risk: %.1f]",
            alert.alert_id,
            alert.threat_class,
            alert.confidence,
            alert.risk_score,
        )
        return alert

    def process_incident(self, incident: Incident) -> Incident:
        """Score incident and persist in store."""
        final_risk = self.calculator.calculate_incident_risk(incident)
        incident.risk_score = final_risk

        self.store.save_incident(incident)

        logger.info(
            "Scored Incident %s: [Chain: %s, Risk: %.1f]",
            incident.incident_id,
            incident.attack_chain.value,
            incident.risk_score,
        )
        return incident
