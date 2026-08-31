"""UDT-X ML Streaming Inference Engine.

Consumes FeatureVector records from `feature-vectors`, applies registered ensemble,
and publishes enriched `ml_score` payloads to `ml-scores`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ingestion.kafka_producer import UDTXKafkaProducer
from ml.explainability.shap_explainer import compute_shap_explanations
from ml.models import MLScorePayload
from ml.models_ensemble import UDTXMLEnsemble
from ml.registry.store import ModelRegistry
from schema.models import FeatureVector

logger = logging.getLogger("udtx.ml.inference")


class MLInferenceEngine:
    """Streaming ML scoring engine consuming feature-vectors."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        input_topic: str = "feature-vectors",
        output_topic: str = "ml-scores",
        group_id: str = "udtx-ml-inference-engine",
        registry_dir: str = "ml/registry",
        dry_run: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.registry_dir = registry_dir
        self.dry_run = dry_run

        # Initialize producer
        self.producer = UDTXKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            topic=output_topic,
            client_id="udtx-ml-inference-producer",
            dry_run=dry_run,
        )

        # Load latest registered model
        self.registry = ModelRegistry(registry_dir=registry_dir)
        self.model = self._load_model()

    def _load_model(self) -> UDTXMLEnsemble:
        meta = self.registry.get_latest_model_meta()
        if meta and meta.get("artifact_path") and Path(meta["artifact_path"]).exists():
            logger.info("Loading registered ML model from %s", meta["artifact_path"])
            return UDTXMLEnsemble.load(meta["artifact_path"])
        logger.info(
            "No registered model artifact found, initializing fresh baseline ensemble."
        )
        model = UDTXMLEnsemble(version="v1.0.0")
        return model

    def score_feature_vector(self, fv: FeatureVector) -> MLScorePayload:
        """Score a FeatureVector and compute SHAP contributions."""
        explanation = compute_shap_explanations(fv, model=self.model)

        is_anom = bool(
            explanation["predicted_class"] != "BENIGN"
            or explanation["ensemble_ml_score"] >= 0.50
        )

        payload = MLScorePayload(
            flow_id=fv.flow_id,
            src_ip=fv.src_ip,
            dst_ip=fv.dst_ip,
            protocol=fv.protocol,
            is_anomaly=is_anom,
            supervised_class=explanation["predicted_class"],
            supervised_probability=explanation["class_probability"],
            anomaly_score=explanation["anomaly_score"],
            ensemble_ml_score=explanation["ensemble_ml_score"],
            top_feature_contributions=explanation["top_feature_contributions"],
            model_version=self.model.version,
        )

        # Emit to output topic
        self.producer.send_event(
            event_dict=payload.model_dump(mode="json"),
            key=fv.src_ip,
        )

        return payload

    def process_raw_message(self, msg_val: Any) -> MLScorePayload | None:
        try:
            if isinstance(msg_val, (bytes, bytearray)):
                data = json.loads(msg_val.decode("utf-8"))
            elif isinstance(msg_val, str):
                data = json.loads(msg_val)
            else:
                data = msg_val
            fv = FeatureVector.model_validate(data)
            return self.score_feature_vector(fv)
        except Exception as exc:
            logger.warning("Failed to score feature vector: %s", exc)
            return None

    def start_consumer(self, max_records: int | None = None) -> None:
        if self.dry_run:
            logger.info("ML Inference Engine running in dry-run mode.")
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
            logger.info("ML Inference Engine subscribed to %s", self.input_topic)
            consumed = 0
            for msg in consumer:
                self.process_raw_message(msg.value)
                consumed += 1
                if max_records and consumed >= max_records:
                    break
        except Exception as exc:
            logger.error("ML Inference Engine consumer error: %s", exc)
