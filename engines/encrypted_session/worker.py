"""UDT-X Encrypted-Session Anomaly Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, inspects TLS/QUIC metadata,
and emits alerts to `raw-alerts` when an encrypted session anomaly is detected.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.encrypted_session.detector import (
    EncryptedSessionDetector,
    EncryptedSessionSignals,
)
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.encrypted_session.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(fv: FeatureVector, signals: EncryptedSessionSignals) -> Alert:
    evidence = [
        EvidenceItem(
            key="ja3_fingerprint",
            value=signals.evidence.get("ja3"),
            description="Client JA3 TLS fingerprint.",
        ),
        EvidenceItem(
            key="ja3_anomaly_score",
            value=signals.ja3_anomaly_score,
            threshold=0.5,
            description="JA3 novelty / malicious / format anomaly score.",
        ),
        EvidenceItem(
            key="packet_sequence_anomaly_score",
            value=signals.packet_sequence_anomaly_score,
            threshold=0.5,
            description="Handshake packet size dynamic anomaly score.",
        ),
        EvidenceItem(
            key="handshake_duration_ms",
            value=signals.evidence.get("handshake_duration_ms"),
            description="Observed TLS handshake duration in milliseconds.",
        ),
    ] + [
        EvidenceItem(key=k, value=v, description=f"TLS evidence: {k}")
        for k, v in signals.evidence.items()
    ]

    mitre = [
        MitreAttack(
            tactic="Command and Control",
            technique_id="T1573.002",
            technique_name="Encrypted Channel: Asymmetric Cryptography",
            url="https://attack.mitre.org/techniques/T1573/002/",
        ),
        MitreAttack(
            tactic="Defense Evasion",
            technique_id="T1027",
            technique_name="Obfuscated Files or Information",
            url="https://attack.mitre.org/techniques/T1027/",
        ),
    ]

    ja3_val = signals.evidence.get("ja3") or "unknown"
    sni_val = signals.evidence.get("sni") or fv.dst_ip

    ja3_rsn = signals.evidence.get("ja3_reason")
    pkt_rsn = signals.evidence.get("packet_sequence_reason")
    description = (
        f"Anomalous TLS/QUIC session detected from {fv.src_ip} to "
        f"{fv.dst_ip} ({sni_val}): JA3 reason='{ja3_rsn}', "
        f"packet sequence reason='{pkt_rsn}'."
    )

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class="ENCRYPTED_ANOMALY",
        severity=_severity_from_confidence(signals.confidence),
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=(
            f"Encrypted Session Anomaly — {fv.src_ip} → {sni_val} "
            f"(ja3={ja3_val[:8]}..., conf={signals.confidence:.0%})"
        ),
        description=description,
    )


class EncryptedSessionEngine:
    """Streaming Encrypted Session Anomaly Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-encrypted-session-engine",
        confidence_threshold: float = 0.50,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        self.detector = EncryptedSessionDetector()
        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def process_feature_vector(self, fv: FeatureVector) -> Alert | None:
        self.vectors_processed += 1

        # Check if flow has TLS metadata
        if not fv.tls:
            return None

        signals = self.detector.evaluate(
            src_ip=fv.src_ip,
            ja3=fv.tls.ja3,
            ja3s=fv.tls.ja3s,
            sni=fv.tls.sni,
            cipher=fv.tls.cipher,
            packet_size_sequence=fv.tls.packet_size_sequence,
            handshake_duration_ms=fv.tls.handshake_duration_ms,
        )

        if signals.is_anomaly or signals.confidence >= self.confidence_threshold:
            alert = _build_alert(fv, signals)
            self.producer.send_event(
                json.loads(alert.model_dump_json()),
                key=f"{fv.src_ip}:encrypted_anomaly",
            )
            self.alerts_emitted += 1
            logger.warning(
                "ENCRYPTED_ANOMALY ALERT: src=%s dst=%s conf=%.2f ja3=%s",
                fv.src_ip,
                fv.dst_ip,
                signals.confidence,
                fv.tls.ja3,
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
            logger.warning("Encrypted session engine error: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Encrypted session engine in dry-run mode.")
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
            logger.info("Encrypted Session Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Encrypted session engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()
