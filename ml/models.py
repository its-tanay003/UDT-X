"""UDT-X ML Data Models, Unified Feature Representation, and Anomaly Models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

# Canonical ordered feature columns used by XGBoost and IsolationForest
FEATURE_COLUMNS: list[str] = [
    "packets_per_sec",
    "bytes_per_sec",
    "packet_size_mean",
    "packet_size_stddev",
    "window_flow_count",
    "window_unique_dst_ips",
    "window_unique_dst_ports",
    "byte_ratio_out_in",
    "packet_ratio_out_in",
    "duration_ms",
    "inter_arrival_time_ms",
    "jitter_ms",
    "periodicity_score",
    "domain_entropy",
    "ngram_score",
    "query_length",
]


class MLScorePayload(BaseModel):
    """Enriched scoring record output by ML Inference engine."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    score_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for ML score record.",
    )
    flow_id: str = Field(..., description="Correlated Flow ID.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of ML inference.",
    )
    src_ip: str = Field(..., description="Source IP address.")
    dst_ip: str = Field(..., description="Destination IP address.")
    protocol: str = Field(..., description="Protocol name.")

    # Model scores
    is_anomaly: bool = Field(
        ..., description="True if anomaly score or classifier crosses threshold."
    )
    supervised_class: str = Field(
        default="BENIGN",
        description="Predicted threat class (BENIGN, DDOS, RECON, C2, DGA, EXFIL).",
    )
    supervised_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="XGBoost classification probability for predicted class.",
    )
    anomaly_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Isolation Forest / Autoencoder normalized anomaly score.",
    )
    ensemble_ml_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fused ML score combining supervised and unsupervised models.",
    )

    # Explainability contributions
    top_feature_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="Feature names and relative SHAP/attribution weights.",
    )
    model_version: str = Field(
        default="v1.0.0", description="Registered model version identifier."
    )
