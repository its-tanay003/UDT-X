"""UDT-X Feature Extraction Streaming Worker.

Consumes canonical `FlowEvent` messages from `flow-events`, maintains
Redis/In-Memory sliding window metrics, computes multidimensional features,
and publishes validated `FeatureVector` records to `feature-vectors`.
"""

import json
import logging
from typing import Any

from features.extractor import (
    calculate_directional_ratios,
    calculate_iat_and_jitter,
    calculate_ngram_anomaly_score,
    calculate_packet_size_stats,
    calculate_periodicity_score,
    calculate_shannon_entropy,
    calculate_throughput_rates,
)
from features.window_store import FlowSnapshot, SlidingWindowStore
from ingestion.kafka_producer import UDTXKafkaProducer
from schema.models import (
    DirectionalFeatures,
    DNSFeatures,
    FeatureVector,
    FlowDirection,
    FlowEvent,
    NetworkFeatures,
    TemporalFeatures,
    TLSFeatures,
)

logger = logging.getLogger("udtx.features.worker")


class FeatureExtractionWorker:
    """Feature Extraction Worker processing FlowEvent streams."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "flow-events",
        output_topic: str = "feature-vectors",
        redis_url: str | None = "redis://localhost:6379/0",
        group_id: str = "udtx-feature-engine",
        window_seconds: int = 60,
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.redis_url = redis_url
        self.group_id = group_id
        self.dry_run = dry_run

        self.window_store = SlidingWindowStore(
            redis_url=redis_url, window_seconds=window_seconds
        )
        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            dry_run=dry_run,
        )

        self.processed_count = 0
        self.error_count = 0

    def extract_features_from_flow(self, flow: FlowEvent) -> FeatureVector:
        """Compute full FeatureVector for a given canonical FlowEvent."""
        ts_ms = flow.timestamp.timestamp() * 1000.0
        src_ip = flow.src_ip

        # 1. Update sliding window store with snapshot
        snapshot = FlowSnapshot(
            flow_id=flow.flow_id,
            timestamp_ms=ts_ms,
            dst_ip=flow.dst_ip,
            dst_port=flow.dst_port,
            protocol=flow.protocol,
            direction=flow.direction.value,
            bytes=flow.bytes,
            packets=flow.packets,
            is_dns=bool(flow.dns and flow.dns.query),
            query=flow.dns.query if flow.dns else "",
        )
        self.window_store.add_flow(src_ip, snapshot)

        # 2. Retrieve active sliding window history
        history = self.window_store.get_window_snapshots(src_ip, ts_ms)

        # 3. Network features
        pps, bps = calculate_throughput_rates(
            flow.bytes, flow.packets, flow.duration_ms
        )
        mean_pkt_sz, std_pkt_sz = calculate_packet_size_stats(flow.bytes, flow.packets)
        unique_dst_ips = len({s.dst_ip for s in history})
        unique_dst_ports = len({s.dst_port for s in history})

        network_feat = NetworkFeatures(
            packets_per_sec=pps,
            bytes_per_sec=bps,
            packet_size_mean=mean_pkt_sz,
            packet_size_stddev=std_pkt_sz,
            window_flow_count=len(history),
            window_unique_dst_ips=unique_dst_ips,
            window_unique_dst_ports=unique_dst_ports,
        )

        # 4. Directional features
        outbound_bytes = sum(
            s.bytes
            for s in history
            if s.direction in (FlowDirection.OUTBOUND, FlowDirection.EXTERNAL)
        )
        inbound_bytes = sum(
            s.bytes for s in history if s.direction == FlowDirection.INBOUND
        )
        outbound_pkts = sum(
            s.packets
            for s in history
            if s.direction in (FlowDirection.OUTBOUND, FlowDirection.EXTERNAL)
        )
        inbound_pkts = sum(
            s.packets for s in history if s.direction == FlowDirection.INBOUND
        )

        byte_ratio, pkt_ratio = calculate_directional_ratios(
            outbound_bytes, inbound_bytes, outbound_pkts, inbound_pkts
        )

        directional_feat = DirectionalFeatures(
            direction=flow.direction,
            outbound_bytes_window=outbound_bytes,
            inbound_bytes_window=inbound_bytes,
            byte_ratio_out_in=byte_ratio,
            packet_ratio_out_in=pkt_ratio,
        )

        # 5. Temporal features
        timestamps = [s.timestamp_ms for s in history]
        iat_ms, jitter_ms = calculate_iat_and_jitter(timestamps)

        # Calculate inter-arrival intervals for autocorrelation periodicity
        intervals = [
            max(0.001, (timestamps[i] - timestamps[i - 1]) / 1000.0)
            for i in range(1, len(timestamps))
        ]
        periodicity = calculate_periodicity_score(intervals)

        temporal_feat = TemporalFeatures(
            duration_ms=flow.duration_ms,
            inter_arrival_time_ms=iat_ms,
            jitter_ms=jitter_ms,
            periodicity_score=periodicity,
        )

        # 6. DNS features (if present)
        dns_feat = None
        if flow.dns and flow.dns.query:
            query = flow.dns.query
            entropy = (
                flow.dns.entropy
                if flow.dns.entropy is not None
                else calculate_shannon_entropy(query)
            )
            ngram_prob = calculate_ngram_anomaly_score(query)
            dns_queries_window = sum(1 for s in history if s.is_dns)

            dns_feat = DNSFeatures(
                query=query,
                query_length=len(query),
                domain_entropy=entropy,
                ngram_score=ngram_prob,
                dns_query_frequency_window=dns_queries_window,
            )

        # 7. TLS features (if present, zero payload decryption)
        tls_feat = None
        if flow.tls:
            tls_feat = TLSFeatures(
                ja3=flow.tls.ja3,
                ja3s=flow.tls.ja3s,
                sni=flow.tls.sni,
                cipher=flow.tls.cipher,
                packet_size_sequence=flow.tls.packet_size_sequence,
                handshake_duration_ms=round(flow.duration_ms * 0.25, 2)
                if flow.duration_ms > 0
                else None,
            )

        return FeatureVector(
            flow_id=flow.flow_id,
            timestamp=flow.timestamp,
            src_ip=flow.src_ip,
            dst_ip=flow.dst_ip,
            protocol=flow.protocol,
            network=network_feat,
            directional=directional_feat,
            temporal=temporal_feat,
            dns=dns_feat,
            tls=tls_feat,
            schema_version="1.0.0",
        )

    def process_raw_message(self, msg_val: Any) -> FeatureVector | None:
        """Parse raw Kafka payload into FlowEvent, extract features, and publish."""
        try:
            if isinstance(msg_val, (bytes, bytearray)):
                data = json.loads(msg_val.decode("utf-8"))
            elif isinstance(msg_val, str):
                data = json.loads(msg_val)
            elif isinstance(msg_val, dict):
                data = msg_val
            else:
                raise ValueError(f"Unsupported message type: {type(msg_val).__name__}")

            flow = FlowEvent.model_validate(data)
            features = self.extract_features_from_flow(flow)

            # Publish to feature-vectors Kafka topic
            feature_payload = json.loads(features.model_dump_json())
            self.producer.send_event(feature_payload, key=features.src_ip)
            self.processed_count += 1
            return features

        except Exception as e:
            self.error_count += 1
            logger.warning("Feature extraction failed for message: %s", e)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        """Start Kafka consumer loop reading flow-events."""
        if self.dry_run:
            logger.info("Worker in dry-run mode; skipping live consumer loop.")
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
            logger.info("Feature Extraction Worker subscribed to %s", self.input_topic)

            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break

        except Exception as e:
            logger.error("Fatal error in Feature Extraction consumer loop: %s", e)
        finally:
            self.producer.flush()
            self.producer.close()
