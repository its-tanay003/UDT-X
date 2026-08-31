"""UDT-X DGA & DNS Tunnelling Detection Engine — Kafka Worker.

Consumes FeatureVector messages from `feature-vectors`, inspects DNS queries,
computes DGA / DNS Tunnelling signals, and emits alerts to `raw-alerts`.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from engines.dga_dns_tunnel.detector import DGADNSTunnelDetector, DNSSignals
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    Alert,
    EvidenceItem,
    FeatureVector,
    MitreAttack,
    SeverityLevel,
)

logger = logging.getLogger("udtx.engines.dga_dns_tunnel.worker")


def _severity_from_confidence(confidence: float) -> SeverityLevel:
    if confidence >= 0.85:
        return SeverityLevel.CRITICAL
    if confidence >= 0.70:
        return SeverityLevel.HIGH
    if confidence >= 0.55:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


def _build_alert(fv: FeatureVector, signals: DNSSignals) -> Alert:
    evidence = [
        EvidenceItem(
            key="domain_entropy",
            value=signals.entropy_score,
            threshold=3.4,
            description="Shannon entropy of the domain string.",
        ),
        EvidenceItem(
            key="ngram_score",
            value=signals.ngram_score,
            threshold=0.5,
            description="N-gram English language model anomaly score.",
        ),
        EvidenceItem(
            key="query_length",
            value=signals.evidence.get("query_length", 0),
            threshold=35,
            description="Character length of the DNS query string.",
        ),
        EvidenceItem(
            key="unique_subdomains_count",
            value=signals.evidence.get("unique_subdomains_count", 0),
            threshold=5,
            description="Count of distinct subdomains queried under the same apex.",
        ),
    ] + [
        EvidenceItem(key=k, value=v, description=f"DNS evidence: {k}")
        for k, v in signals.evidence.items()
    ]

    if signals.threat_class == "DNS_TUNNELING":
        mitre = [
            MitreAttack(
                tactic="Exfiltration",
                technique_id="T1048.003",
                technique_name="Exfiltration Over Unencrypted Non-C2 Protocol: DNS",
                url="https://attack.mitre.org/techniques/T1048/003/",
            ),
            MitreAttack(
                tactic="Command and Control",
                technique_id="T1071.004",
                technique_name="Application Layer Protocol: DNS",
                url="https://attack.mitre.org/techniques/T1071/004/",
            ),
        ]
        title = (
            f"DNS Tunnelling / Exfiltration Detected — {fv.src_ip} "
            f"(query='{signals.evidence.get('query')}', conf={signals.confidence:.0%})"
        )
        apex = signals.evidence.get("apex_domain")
        q_len = signals.evidence.get("query_length")
        u_subs = signals.evidence.get("unique_subdomains_count")
        sub_ent = signals.evidence.get("subdomain_entropy")
        desc = (
            f"Host {fv.src_ip} is exhibiting DNS data tunnelling patterns to apex "
            f"'{apex}': length={q_len}, unique subdomains={u_subs}, "
            f"subdomain entropy={sub_ent}."
        )
    else:  # DGA
        mitre = [
            MitreAttack(
                tactic="Command and Control",
                technique_id="T1568.002",
                technique_name="Dynamic Resolution: Domain Generation Algorithms",
                url="https://attack.mitre.org/techniques/T1568/002/",
            ),
        ]
        q_str = signals.evidence.get("query")
        title = (
            f"DGA Domain Query Detected — {fv.src_ip} "
            f"(domain='{q_str}', entropy={signals.entropy_score:.2f}, "
            f"ngram={signals.ngram_score:.2f}, conf={signals.confidence:.0%})"
        )
        desc = (
            f"Host {fv.src_ip} queried suspicious algorithmically generated domain "
            f"'{q_str}': Shannon entropy={signals.entropy_score:.2f}, "
            f"n-gram anomaly score={signals.ngram_score:.2f}."
        )

    return Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=fv.timestamp,
        flow_id=fv.flow_id,
        src_ip=fv.src_ip,
        dst_ip=fv.dst_ip,
        protocol=fv.protocol,
        threat_class=signals.threat_class,
        severity=_severity_from_confidence(signals.confidence),
        confidence=round(signals.confidence, 4),
        risk_score=round(signals.confidence * 100.0, 2),
        evidence=evidence,
        mitre=mitre,
        title=title,
        description=desc,
    )


class DGADNSTunnelEngine:
    """Streaming DGA & DNS Tunnelling Detection Engine."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "raw-alerts",
        group_id: str = "udtx-dga-dns-tunnel-engine",
        confidence_threshold: float = 0.50,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run

        self.detector = DGADNSTunnelDetector()
        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.alerts_emitted: int = 0
        self.vectors_processed: int = 0

    def process_feature_vector(self, fv: FeatureVector) -> Alert | None:
        self.vectors_processed += 1

        # Check if flow has DNS metadata
        query = None
        entropy = None
        ngram = None
        q_len = None
        q_freq = None

        if fv.dns:
            query = fv.dns.query
            entropy = fv.dns.domain_entropy
            ngram = fv.dns.ngram_score
            q_len = fv.dns.query_length
            q_freq = fv.dns.dns_query_frequency_window

        if not query:
            return None

        signals = self.detector.evaluate(
            src_ip=fv.src_ip,
            query=query,
            domain_entropy=entropy,
            ngram_score=ngram,
            query_length=q_len,
            query_frequency=q_freq,
        )

        if (
            signals.threat_class in ("DGA", "DNS_TUNNELING")
            and signals.confidence >= self.confidence_threshold
        ):
            alert = _build_alert(fv, signals)
            self.producer.send_event(
                json.loads(alert.model_dump_json()),
                key=f"{fv.src_ip}:{signals.threat_class}",
            )
            self.alerts_emitted += 1
            logger.warning(
                "%s ALERT: src=%s query=%s conf=%.2f entropy=%.2f ngram=%.2f",
                signals.threat_class,
                fv.src_ip,
                query,
                signals.confidence,
                signals.entropy_score,
                signals.ngram_score,
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
            logger.warning("DGA/DNS Tunnel engine error: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("DGA/DNS Tunnel engine in dry-run mode.")
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
            logger.info("DGA/DNS Tunnel Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("DGA/DNS Tunnel engine consumer error: %s", exc)
        finally:
            self.producer.flush()
            self.producer.close()
