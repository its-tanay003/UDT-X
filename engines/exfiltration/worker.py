"""UDT-X Data Exfiltration Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, inspects metrics,
and emits alerts to `raw-alerts` when data exfiltration patterns are detected.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.exfiltration.detector import (
    ExfiltrationDetector,
    ExfiltrationSignals,
)
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.exfiltration.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(fv: FeatureVector, signals: ExfiltrationSignals) -> Alert:
    evidence = [
        EvidenceItem(
            key="outbound_bytes",
            value=signals.evidence.get("outbound_bytes"),
            threshold=100000,
            description="Outbound transfer volume in bytes.",
        ),
        EvidenceItem(
            key="byte_ratio_out_in",
            value=signals.evidence.get("byte_ratio"),
            threshold=10.0,
            description="Outbound to inbound byte ratio.",
        ),
        EvidenceItem(
            key="is_novel_destination",
            value=signals.evidence.get("is_novel_destination"),
            description="Flag indicating first-time connection to destination.",
        ),
        EvidenceItem(
            key="size_zscore",
            value=signals.evidence.get("size_zscore"),
            threshold=3.0,
            description="Standard deviations above historical transfer size baseline.",
        ),
    ] + [
        EvidenceItem(key=k, value=v, description=f"Exfil evidence: {k}")
        for k, v in signals.evidence.items()
    ]

    mitre = [
        MitreAttack(
            tactic="Exfiltration",
            technique_id="T1048",
            technique_name="Exfiltration Over Alternative Protocol",
            url="https://attack.mitre.org/techniques/T1048/",
        ),
        MitreAttack(
            tactic="Exfiltration",
            technique_id="T1041",
            technique_name="Exfiltration Over C2 Channel",
            url="https://attack.mitre.org/techniques/T1041/",
        ),
    ]

    out_mb = signals.evidence.get("outbound_bytes", 0) / (1024 * 1024)
    ratio = signals.evidence.get("byte_ratio", 0)
    is_nov = signals.evidence.get("is_novel_destination")
    z_scr = signals.evidence.get("size_zscore")
    description = (
        f"Potential data exfiltration detected from {fv.src_ip} to {fv.dst_ip}: "
        f"Transferred {out_mb:.1f} MB outbound with ratio={ratio:.1f}. "
        f"Novel destination={is_nov}, Size Z-Score={z_scr}."
    )

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class="EXFILTRATION",
        severity=_severity_from_confidence(signals.confidence),
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=(
            f"Data Exfiltration Detected — {fv.src_ip} → {fv.dst_ip} "
            f"({out_mb:.1f}MB, ratio={ratio:.1f}, conf={signals.confidence:.0%})"
        ),
        description=description,
    )


class ExfiltrationEngine:
    """Streaming Data Exfiltration Detection Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-exfiltration-engine",
        confidence_threshold: float = 0.50,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        self.detector = ExfiltrationDetector()
        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def process_feature_vector(self, fv: FeatureVector) -> Alert | None:
        self.vectors_processed += 1

        out_bytes = float(fv.directional.outbound_bytes_window)
        in_bytes = float(fv.directional.inbound_bytes_window)
        ratio = fv.directional.byte_ratio_out_in

        signals = self.detector.evaluate(
            src_ip=fv.src_ip,
            dst_ip=fv.dst_ip,
            outbound_bytes=out_bytes,
            inbound_bytes=in_bytes,
            byte_ratio=ratio,
            timestamp=fv.timestamp,
        )

        if signals.is_anomaly or signals.confidence >= self.confidence_threshold:
            alert = _build_alert(fv, signals)
            self.producer.send_event(
                json.loads(alert.model_dump_json()),
                key=f"{fv.src_ip}:exfiltration",
            )
            self.alerts_emitted += 1
            logger.warning(
                "EXFILTRATION ALERT: src=%s dst=%s conf=%.2f out_bytes=%.0f",
                fv.src_ip,
                fv.dst_ip,
                signals.confidence,
                out_bytes,
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
            logger.warning("Exfiltration engine error: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Exfiltration engine in dry-run mode.")
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
            logger.info("Exfiltration Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Exfiltration engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()
