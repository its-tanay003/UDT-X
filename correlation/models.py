"""UDT-X Incident & Graph Models for Temporal Correlation (Phase 8).

Defines canonical Incident schemas representing multi-alert attack campaigns,
attack chain progressions, and graph relationship entities.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from schema.models import MitreAttack, SeverityLevel


class IncidentStatus(StrEnum):
    """Lifecycle status of a correlated incident."""

    NEW = "new"
    ACTIVE = "active"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AttackChainProgression(StrEnum):
    """Detected kill-chain or multi-stage progression pattern."""

    RECON_TO_C2 = "RECONNAISSANCE -> C2_BEACONING"
    C2_TO_EXFIL = "C2_BEACONING -> EXFILTRATION"
    FULL_KILL_CHAIN = "RECONNAISSANCE -> C2_BEACONING -> EXFILTRATION"
    DNS_EXFILTRATION = "DGA/DNS_TUNNEL -> EXFILTRATION"
    DDOS_DISTRACTION = "RECONNAISSANCE -> DDOS"
    GENERIC_MULTI_ALERT = "MULTI_STAGE_ATTACK"


class Incident(BaseModel):
    """Correlated security incident aggregating multiple raw alerts."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    incident_id: str = Field(
        default_factory=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}",
        description="Unique Incident identifier.",
    )
    title: str = Field(..., description="Human-readable incident summary.")
    status: IncidentStatus = Field(
        default=IncidentStatus.NEW, description="Current incident status."
    )
    severity: SeverityLevel = Field(
        default=SeverityLevel.MEDIUM, description="Computed incident severity."
    )
    risk_score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Composite incident risk score (0.0 to 100.0).",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Incident creation timestamp.",
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of most recent alert added to incident.",
    )

    # Core entities involved
    primary_host_ip: str = Field(
        ..., description="Primary source or compromised host IP."
    )
    target_destination_ips: list[str] = Field(
        default_factory=list,
        description="Distinct destination IPs touched in incident.",
    )

    # Aggregated alerts
    alert_ids: list[str] = Field(
        default_factory=list,
        description="IDs of all raw alerts forming incident.",
    )
    threat_classes: list[str] = Field(
        default_factory=list, description="Distinct threat classes observed."
    )
    mitre_techniques: list[MitreAttack] = Field(
        default_factory=list, description="Aggregated MITRE ATT&CK techniques."
    )

    # Attack Progression Tagging
    attack_chain: AttackChainProgression | None = Field(
        default=None,
        description="Detected kill chain pattern sequence tag.",
    )
    summary: str = Field(
        default="", description="Detailed contextual summary of attack stages."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Forensic context and graph node IDs.",
    )
