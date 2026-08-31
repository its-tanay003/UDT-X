"""UDT-X Reconnaissance Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, maintains
per-source ReconDetector state, and emits Alert records to `raw-alerts`
when the composite reconnaissance confidence score exceeds threshold.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.recon.detector import ReconDetector, ReconSignals
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.recon.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(fv: FeatureVector, signals: ReconSignals) -> Alert:
    evidence = [
        EvidenceItem(
            key=k,
            value=v,
            description=f"Recon signal: {k}",
        )
        for k, v in signals.evidence.items()
    ] + [
        EvidenceItem(
            key="fanout_score",
            value=signals.fanout_score,
            threshold=0.5,
            description="Host/port fan-out sub-score",
        ),
        EvidenceItem(
            key="sequential_score",
            value=signals.sequential_score,
            threshold=0.5,
            description="Sequential port-scan pattern sub-score",
        ),
        EvidenceItem(
            key="probe_score",
            value=signals.probe_score,
            threshold=0.5,
            description="Low-byte / high-connection probe signature sub-score",
        ),
    ]

    mitre = [
        MitreAttack(
            tactic="Discovery",
            technique_id="T1046",
            technique_name="Network Service Discovery",
            url="https://attack.mitre.org/techniques/T1046/",
        ),
        MitreAttack(
            tactic="Reconnaissance",
            technique_id="T1595",
            technique_name="Active Scanning",
            url="https://attack.mitre.org/techniques/T1595/",
        ),
        MitreAttack(
            tactic="Reconnaissance",
            technique_id="T1595.002",
            technique_name="Vulnerability Scanning",
            url="https://attack.mitre.org/techniques/T1595/002/",
        ),
    ]

    fan_out_count = signals.evidence.get("fan_out_count", 0)
    scan_rate = signals.evidence.get("scan_rate", 0)

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class="RECONNAISSANCE",
        severity=_severity_from_confidence(signals.confidence),
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=(
            f"Reconnaissance Detected — {fv.src_ip} "
            f"(fan-out={fan_out_count}, scan_rate={scan_rate:.1f}, "
            f"confidence={signals.confidence:.0%})"
        ),
        description=(
            f"Source {fv.src_ip} exhibiting scanning behaviour: "
            f"fan-out count={fan_out_count} unique targets, "
            f"sequential port score={signals.sequential_score:.2f}, "
            f"probe signature score={signals.probe_score:.2f}."
        ),
    )


class ReconEngine:
    """Streaming Reconnaissance Detection Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-recon-engine",
        confidence_threshold: float = 0.45,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        # Per-source state
        self._detectors: dict[str, ReconDetector] = {}

        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def _get_detector(self, src_ip: str) -> ReconDetector:
        if src_ip not in self._detectors:
            self._detectors[src_ip] = ReconDetector(src_ip=src_ip)
        return self._detectors[src_ip]

    def _bytes_per_flow(self, fv: FeatureVector) -> float:
        """Estimate bytes per individual flow from window aggregate."""
        count = max(1, fv.network.window_flow_count)
        # bytes_per_sec * duration gives total bytes in this flow
        total_bytes = fv.network.bytes_per_sec * max(
            fv.temporal.duration_ms / 1000.0, 0.001
        )
        return total_bytes / count

    def process_feature_vector(self, fv: FeatureVector) -> Alert | None:
        self.vectors_processed += 1
        detector = self._get_detector(fv.src_ip)

        # dst_port: use src_port as proxy when dst not available in fv schema
        # FeatureVector doesn't carry dst_port directly — use unique_dst_ports
        # as the scan-range proxy, and derive a representative port value from
        # the flow_id or fall back to 0.
        dst_port = _extract_dst_port(fv)

        signals = detector.evaluate(
            dst_ip=fv.dst_ip,
            dst_port=dst_port,
            unique_dst_ips=fv.network.window_unique_dst_ips,
            unique_dst_ports=fv.network.window_unique_dst_ports,
            bytes_per_flow=self._bytes_per_flow(fv),
            window_flow_count=fv.network.window_flow_count,
            packet_size_mean=fv.network.packet_size_mean,
        )

        if signals.confidence >= self.confidence_threshold:
            alert = _build_alert(fv, signals)
            self.producer.send_event(
                json.loads(alert.model_dump_json()),
                key=fv.src_ip,
            )
            self.alerts_emitted += 1
            logger.warning(
                "RECON ALERT: src=%s conf=%.2f fan-out=%s seq=%.2f",
                fv.src_ip,
                signals.confidence,
                signals.evidence.get("fan_out_count"),
                signals.sequential_score,
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
            logger.warning("Recon engine failed to process message: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("Recon engine in dry-run mode.")
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
            logger.info("Recon Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("Recon engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()


def _extract_dst_port(fv: FeatureVector) -> int:
    """
    Best-effort extraction of a representative destination port.

    FeatureVector does not carry a per-flow dst_port field (that lives in
    FlowEvent).  We derive a stable synthetic port from the flow_id hash so
    that the sequential-scan detector receives a consistent, varied stream of
    values during replay.  In production the engine should be extended to
    receive dst_port directly via a richer FeatureVector schema.
    """
    try:
        # flow_id often carries port info like "flow-10.0.0.1:54321->..."
        parts = fv.flow_id.replace("->", ":").split(":")
        for part in reversed(parts):
            candidate = int(part)
            if 1 <= candidate <= 65535:
                return candidate
    except (ValueError, IndexError):
        pass
    # Deterministic fallback: hash of flow_id modulo port space
    return (hash(fv.flow_id) % 65534) + 1
