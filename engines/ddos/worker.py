"""UDT-X DDoS Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, maintains
per-destination DDoSDetector state, and emits Alert records to `raw-alerts`
when the composite DDoS confidence score exceeds the configured threshold.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.ddos.detector import DDoSDetector, DDoSSignals
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.ddos.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(
    fv: FeatureVector,
    signals: DDoSSignals,
) -> Alert:
    """Construct an Alert record from a triggered DDoS signal set."""
    evidence = [
        EvidenceItem(
            key=k,
            value=v,
            description=f"DDoS signal: {k}",
        )
        for k, v in signals.evidence.items()
    ] + [
        EvidenceItem(
            key="throughput_score",
            value=signals.throughput_score,
            threshold=0.5,
            description="Normalised throughput anomaly sub-score",
        ),
        EvidenceItem(
            key="entropy_score",
            value=signals.entropy_score,
            threshold=0.5,
            description="Source-IP entropy collapse sub-score",
        ),
        EvidenceItem(
            key="protocol_score",
            value=signals.protocol_score,
            threshold=0.5,
            description="Protocol imbalance (UDP/ICMP flood) sub-score",
        ),
    ]

    mitre = [
        MitreAttack(
            tactic="Impact",
            technique_id="T1498",
            technique_name="Network Denial of Service",
            url="https://attack.mitre.org/techniques/T1498/",
        ),
        MitreAttack(
            tactic="Impact",
            technique_id="T1498.001",
            technique_name="Direct Network Flood",
            url="https://attack.mitre.org/techniques/T1498/001/",
        ),
    ]

    severity = _severity_from_confidence(signals.confidence)

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class="DDOS",
        severity=severity,
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=f"DDoS Detected — {fv.dst_ip} (confidence {signals.confidence:.0%})",
        description=(
            f"Sustained high-volume traffic targeting {fv.dst_ip} from "
            f"{fv.src_ip}. Throughput z-score={signals.throughput_z:.1f}, "
            f"src entropy={signals.evidence.get('src_entropy', 'N/A')}, "
            f"protocol={fv.protocol}."
        ),
    )


class DDoSEngine:
    """Streaming DDoS Detection Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-ddos-engine",
        confidence_threshold: float = 0.50,
        ewma_alpha: float = 0.2,
        warmup_samples: int = 5,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.ewma_alpha = ewma_alpha
        self.warmup_samples = warmup_samples
        self.dry_run = dry_run

        # Per-destination state
        self._detectors: dict[str, DDoSDetector] = {}

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def _get_detector(self, dst_ip: str) -> DDoSDetector:
        if dst_ip not in self._detectors:
            self._detectors[dst_ip] = DDoSDetector(
                dst_ip=dst_ip,
                ewma_alpha=self.ewma_alpha,
                warmup_samples=self.warmup_samples,
            )
        return self._detectors[dst_ip]

    def process_feature_vector(self, fv: FeatureVector) -> Alert | None:
        """Evaluate a FeatureVector, emit an Alert if DDoS is detected."""
        self.vectors_processed += 1
        detector = self._get_detector(fv.dst_ip)

        signals = detector.evaluate(
            src_ip=fv.src_ip,
            protocol=fv.protocol,
            pps=fv.network.packets_per_sec,
            bps=fv.network.bytes_per_sec,
        )

        if signals.confidence >= self.confidence_threshold:
            alert = _build_alert(fv, signals)
            payload = json.loads(alert.model_dump_json())
            self.producer.send_event(payload, key=fv.dst_ip)
            self.alerts_emitted += 1
            logger.warning(
                "DDoS ALERT: dst=%s confidence=%.2f severity=%s",
                fv.dst_ip,
                signals.confidence,
                alert.severity,
            )
            return alert

        return None

    def process_raw_message(self, msg_val: Any) -> Alert | None:
        """Parse Kafka message payload and evaluate."""
        try:
            if isinstance(msg_val, (bytes, bytearray)):
                data = json.loads(msg_val.decode("utf-8"))
            elif isinstance(msg_val, str):
                data = json.loads(msg_val)
            else:
                data = msg_val
            fv = FeatureVector.model_validate(data)
            return self.process_feature_vector(fv)
        except Exception as exc:
            logger.warning("DDoS engine failed to process message: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        """Start Kafka consumer loop."""
        if self.dry_run:
            logger.info("DDoS engine in dry-run mode.")
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
            logger.info("DDoS Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("DDoS engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()
