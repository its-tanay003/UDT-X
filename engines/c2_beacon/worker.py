"""UDT-X C2 Beaconing Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, evaluates each
against the C2BeaconDetector, and emits Alert records to `raw-alerts`
when the composite beaconing confidence exceeds the configured threshold.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.c2_beacon.detector import BeaconSignals, C2BeaconDetector
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.c2_beacon.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(fv: FeatureVector, signals: BeaconSignals) -> Alert:
    """Construct a fully-populated Alert from a FeatureVector + BeaconSignals."""
    evidence = [
        EvidenceItem(
            key="periodicity_score",
            value=signals.periodicity_score,
            threshold=0.45,
            description=(
                "Combined periodicity × jitter sub-score. "
                "Pure beacon → 1.0; irregular polling → near 0."
            ),
        ),
        EvidenceItem(
            key="persistence_score",
            value=signals.persistence_score,
            threshold=0.35,
            description=(
                f"Destination persistence sub-score for {fv.src_ip} → {fv.dst_ip}. "
                f"Contacts: {signals.contact_count}, "
                f"window: {signals.observation_secs:.0f}s."
            ),
        ),
        EvidenceItem(
            key="payload_score",
            value=signals.payload_score,
            threshold=0.20,
            description=(
                "Small / consistent payload sub-score. "
                "Beacon-sized packets → high; HTTP body → low."
            ),
        ),
    ] + [
        EvidenceItem(key=k, value=v, description=f"C2 beacon evidence: {k}")
        for k, v in signals.evidence.items()
    ]

    mitre = [
        MitreAttack(
            tactic="Command and Control",
            technique_id="T1071",
            technique_name="Application Layer Protocol",
            url="https://attack.mitre.org/techniques/T1071/",
        ),
        MitreAttack(
            tactic="Command and Control",
            technique_id="T1571",
            technique_name="Non-Standard Port",
            url="https://attack.mitre.org/techniques/T1571/",
        ),
        MitreAttack(
            tactic="Command and Control",
            technique_id="T1132",
            technique_name="Data Encoding",
            url="https://attack.mitre.org/techniques/T1132/",
        ),
    ]

    periodicity_pct = f"{signals.evidence.get('raw_periodicity_score', 0):.0%}"
    jitter = signals.evidence.get("jitter_ms", 0)

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class="C2_BEACONING",
        severity=_severity_from_confidence(signals.confidence),
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=(
            f"C2 Beacon Detected — {fv.src_ip} → {fv.dst_ip} "
            f"(periodicity={periodicity_pct}, contacts={signals.contact_count}, "
            f"jitter={jitter:.0f}ms, conf={signals.confidence:.0%})"
        ),
        description=(
            f"Host {fv.src_ip} exhibits high-regularity beaconing behaviour "
            f"toward {fv.dst_ip}: autocorrelation periodicity "
            f"{periodicity_pct}, jitter {jitter:.0f} ms, "
            f"{signals.contact_count} contacts over "
            f"{signals.observation_secs:.0f}s. "
            "Consistent small payloads suggest C2 keep-alive traffic."
        ),
    )


class C2BeaconEngine:
    """Streaming C2 Beaconing Detection Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-c2-beacon-engine",
        confidence_threshold: float = 0.50,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        self.detector = C2BeaconDetector()

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def process_feature_vector(
        self,
        fv: FeatureVector,
        now: float | None = None,
    ) -> Alert | None:
        self.vectors_processed += 1

        signals = self.detector.evaluate(
            src_ip=fv.src_ip,
            dst_ip=fv.dst_ip,
            periodicity_score=fv.temporal.periodicity_score,
            jitter_ms=fv.temporal.jitter_ms,
            packet_size_mean=fv.network.packet_size_mean,
            packet_size_stddev=fv.network.packet_size_stddev,
            now=now,
        )

        if signals.confidence >= self.confidence_threshold:
            alert = _build_alert(fv, signals)
            self.producer.send_event(
                json.loads(alert.model_dump_json()),
                key=f"{fv.src_ip}:{fv.dst_ip}",
            )
            self.alerts_emitted += 1
            logger.warning(
                "C2 BEACON ALERT: %s → %s  conf=%.2f  "
                "periodicity=%.2f  contacts=%d  jitter=%.0fms",
                fv.src_ip,
                fv.dst_ip,
                signals.confidence,
                signals.periodicity_score,
                signals.contact_count,
                fv.temporal.jitter_ms,
            )
            return alert

        return None

    def process_raw_message(self, msg_val: Any) -> Alert | None:
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
            logger.warning("C2 beacon engine failed to process message: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("C2 Beacon engine in dry-run mode.")
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
            logger.info("C2 Beacon Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("C2 beacon engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()
