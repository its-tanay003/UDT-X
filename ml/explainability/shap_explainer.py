"""UDT-X SHAP & Feature Explainability Engine.

Computes exact feature attributions and SHAP contribution breakdowns
for scored alerts and feature vectors to power the Evidence Explorer.
"""

from __future__ import annotations

from typing import Any

from ml.models import FEATURE_COLUMNS
from ml.models_ensemble import UDTXMLEnsemble
from schema.models import Alert, EvidenceItem, FeatureVector


def compute_shap_explanations(
    feature_vector: FeatureVector,
    model: UDTXMLEnsemble | None = None,
) -> dict[str, Any]:
    """Compute feature importance attribution values for a given FeatureVector."""
    # Extract canonical vector
    net = feature_vector.network
    dir_ = feature_vector.directional
    temp = feature_vector.temporal
    dns = feature_vector.dns

    row = [
        net.packets_per_sec,
        net.bytes_per_sec,
        net.packet_size_mean,
        net.packet_size_stddev,
        float(net.window_flow_count),
        float(net.window_unique_dst_ips),
        float(net.window_unique_dst_ports),
        dir_.byte_ratio_out_in,
        dir_.packet_ratio_out_in,
        temp.duration_ms,
        temp.inter_arrival_time_ms,
        temp.jitter_ms,
        temp.periodicity_score,
        dns.domain_entropy if (dns and dns.domain_entropy is not None) else 0.0,
        dns.ngram_score if (dns and dns.ngram_score is not None) else 0.0,
        float(dns.query_length) if (dns and dns.query_length is not None) else 0.0,
    ]

    if model is None:
        model = UDTXMLEnsemble()

    pred_class, prob, anom, ml_score, shap_dict = model.predict_single(row)

    # Sort contributions in descending order
    sorted_shap = dict(
        sorted(shap_dict.items(), key=lambda item: item[1], reverse=True)
    )

    return {
        "predicted_class": pred_class,
        "class_probability": prob,
        "anomaly_score": anom,
        "ensemble_ml_score": ml_score,
        "top_feature_contributions": sorted_shap,
        "feature_vector_summary": {
            k: v for k, v in zip(FEATURE_COLUMNS, row, strict=False)
        },
    }


def explain_alert(
    alert: Alert, model: UDTXMLEnsemble | None = None
) -> list[EvidenceItem]:
    """Convert alert evidence or attributes into explainability evidence items."""
    evidence_items: list[EvidenceItem] = []
    evidence_items.append(
        EvidenceItem(
            name="ML_THREAT_CLASS_ATTRIBUTION",
            value=alert.threat_class,
            context={"confidence": alert.confidence},
        )
    )
    return evidence_items
