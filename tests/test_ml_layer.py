"""UDT-X ML / Anomaly Layer — Unit & Training Pipeline Tests.

Tests:
1. Multi-dataset generator creates balanced multi-class dataset.
2. Strict time-based train/test split.
3. Training pipeline meets Section 26.6 targets (Precision >= 0.90, Recall >= 0.85).
4. Model Registry logs run metadata and saves artifacts.
5. SHAP explainer extracts root-cause feature contributions.
6. Streaming ML Inference scores FeatureVector and publishes MLScorePayload.
"""

from __future__ import annotations

import tempfile

from ml.explainability.shap_explainer import compute_shap_explanations
from ml.inference.worker import MLInferenceEngine
from ml.models import FEATURE_COLUMNS, MLScorePayload
from ml.models_ensemble import UDTXMLEnsemble
from ml.registry.store import ModelRegistry
from ml.training.dataset_loader import MultiDatasetLoader
from ml.training.train import run_training_pipeline
from schema.models import FeatureVector, NetworkFeatures, TemporalFeatures


def test_dataset_loader_and_time_split() -> None:
    loader = MultiDatasetLoader(seed=123)
    X, y, labels, timestamps = loader.generate_unified_dataset(samples_per_dataset=50)

    assert X.shape == (200, len(FEATURE_COLUMNS))
    assert len(y) == 200
    assert len(labels) == 200
    assert len(timestamps) == 200

    X_train, X_test, y_train, y_test, l_train, l_test = loader.time_based_split(
        X, y, labels, timestamps, train_ratio=0.70
    )
    assert len(X_train) == 140
    assert len(X_test) == 60


def test_training_pipeline_and_metrics_targets() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        res = run_training_pipeline(
            version="v1.0.0-test",
            registry_dir=tmpdir,
            samples_per_dataset=150,
        )

        metrics = res["metrics"]
        assert metrics["precision"] >= 0.90, f"Precision failed target: {metrics}"
        assert metrics["recall"] >= 0.85, f"Recall failed target: {metrics}"
        assert metrics["false_positive_rate"] <= 0.05, f"FPR failed target: {metrics}"

        # Verify registry logged run
        reg = ModelRegistry(registry_dir=tmpdir)
        meta = reg.get_latest_model_meta()
        assert meta is not None
        assert meta["version"] == "v1.0.0-test"
        assert meta["metrics"]["precision"] >= 0.90


def test_shap_explainer_on_ddos_feature_vector() -> None:
    # Train quick model
    loader = MultiDatasetLoader(seed=42)
    X, y, labels, ts = loader.generate_unified_dataset(samples_per_dataset=100)
    X_train, X_test, y_train, y_test, l_train, l_test = loader.time_based_split(
        X, y, labels, ts, train_ratio=0.70
    )
    model = UDTXMLEnsemble(version="v1.0.0")
    model.fit(X_train, y_train, l_train)

    # Synthetic DDoS FeatureVector
    fv_ddos = FeatureVector(
        flow_id="fv-ddos-test-1",
        src_ip="192.168.1.50",
        dst_ip="10.0.0.1",
        protocol="UDP",
        network=NetworkFeatures(
            packets_per_sec=2500.0,
            bytes_per_sec=1_200_000.0,
            packet_size_mean=480.0,
            window_flow_count=600,
        ),
    )

    explanation = compute_shap_explanations(fv_ddos, model=model)
    assert explanation["predicted_class"] == "DDOS"
    assert explanation["class_probability"] >= 0.80
    assert explanation["ensemble_ml_score"] >= 0.70
    assert "packets_per_sec" in explanation["top_feature_contributions"]


def test_ml_streaming_inference_worker() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Pre-train and save a model in registry
        run_training_pipeline(
            version="v1.0.0",
            registry_dir=tmpdir,
            samples_per_dataset=100,
        )

        engine = MLInferenceEngine(
            registry_dir=tmpdir,
            dry_run=True,
        )

        fv = FeatureVector(
            flow_id="fv-c2-test",
            src_ip="192.168.1.99",
            dst_ip="203.0.113.5",
            protocol="TCP",
            network=NetworkFeatures(
                packet_size_mean=110.0,
            ),
            temporal=TemporalFeatures(
                periodicity_score=0.96,
                jitter_ms=1.2,
            ),
        )

        score_payload = engine.score_feature_vector(fv)
        assert isinstance(score_payload, MLScorePayload)
        assert score_payload.supervised_class == "C2"
        assert score_payload.is_anomaly is True
        assert score_payload.ensemble_ml_score >= 0.60
        assert "periodicity_score" in score_payload.top_feature_contributions
