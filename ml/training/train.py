"""UDT-X Training Pipeline & Model Evaluation.

Trains supervised XGBoost/Decision classifier and Isolation Forest anomaly detector
against CIDDS-001, CIC-IDS2017, UNSW-NB15, and CTU-13.
Evaluates against Ideation Section 26.6 targets:
  - Precision >= 0.90
  - Recall >= 0.85
  - False Positive Rate (FPR) < 2%
Logs runs and model artifacts to ml/registry/.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from ml.models import FEATURE_COLUMNS
from ml.models_ensemble import UDTXMLEnsemble
from ml.registry.store import ModelRegistry
from ml.training.dataset_loader import MultiDatasetLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.ml.trainer")


def evaluate_model_metrics(
    model: UDTXMLEnsemble,
    X_test: np.ndarray,
    y_test: np.ndarray,
    labels_test: list[str],
) -> dict[str, float]:
    """Calculate precision, recall, F1, accuracy, and False Positive Rate."""
    tp, fp, tn, fn = 0, 0, 0, 0

    for i in range(len(X_test)):
        row = X_test[i].tolist()
        true_y = y_test[i]

        pred_class, prob, anom, ensemble_score, _ = model.predict_single(row)
        pred_y = 1 if (pred_class != "BENIGN" or ensemble_score >= 0.50) else 0

        if true_y == 1 and pred_y == 1:
            tp += 1
        elif true_y == 0 and pred_y == 1:
            fp += 1
        elif true_y == 0 and pred_y == 0:
            tn += 1
        elif true_y == 1 and pred_y == 0:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    accuracy = (tp + tn) / len(X_test) if len(X_test) > 0 else 1.0

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "false_positive_rate": round(float(fpr), 4),
        "accuracy": round(float(accuracy), 4),
        "tp": float(tp),
        "fp": float(fp),
        "tn": float(tn),
        "fn": float(fn),
    }


def run_training_pipeline(
    version: str = "v1.0.0",
    registry_dir: str = "ml/registry",
    samples_per_dataset: int = 500,
) -> dict[str, Any]:
    """Execute end-to-end dataset loading, time-based split, fitting, and evaluation."""
    logger.info("1. Loading datasets (CIDDS-001, CIC-IDS2017, UNSW-NB15, CTU-13)...")
    loader = MultiDatasetLoader(seed=42)
    X, y, labels, timestamps = loader.generate_unified_dataset(
        samples_per_dataset=samples_per_dataset
    )

    logger.info("2. Performing time-based train/test split (70/30)...")
    split_res = loader.time_based_split(X, y, labels, timestamps, train_ratio=0.70)
    X_train, X_test, y_train, y_test, labels_train, labels_test = split_res
    logger.info(
        "   Train set: %d samples | Test set: %d samples",
        len(X_train),
        len(X_test),
    )

    logger.info("3. Fitting UDT-X ML Ensemble (XGBoost + Anomaly Detector)...")
    model = UDTXMLEnsemble(version=version)
    model.fit(X_train, y_train, labels_train)

    logger.info("4. Evaluating metrics against Ideation Section 26.6 targets...")
    metrics = evaluate_model_metrics(model, X_test, y_test, labels_test)
    logger.info("   Precision : %.2f%% (Target >= 90.0%%)", metrics["precision"] * 100)
    logger.info("   Recall    : %.2f%% (Target >= 85.0%%)", metrics["recall"] * 100)
    logger.info("   F1 Score  : %.2f%%", metrics["f1_score"] * 100)
    logger.info(
        "   FPR       : %.2f%% (Target < 2.0%%)",
        metrics["false_positive_rate"] * 100,
    )

    # Save model artifact
    reg = ModelRegistry(registry_dir=registry_dir)
    artifact_path = Path(registry_dir) / f"model_{version}.json"
    model.save(artifact_path)

    # Log run to registry
    run_info = reg.log_run(
        model_name="udtx_ensemble",
        version=version,
        datasets=loader.DATASET_NAMES,
        features=FEATURE_COLUMNS,
        metrics=metrics,
        parameters={"train_ratio": 0.70, "anomaly_percentile": 98.0},
        model_artifact_path=artifact_path,
    )
    logger.info("5. Model %s successfully logged to registry!", version)
    return {"metrics": metrics, "run_info": run_info, "model": model}


if __name__ == "__main__":
    run_training_pipeline()
