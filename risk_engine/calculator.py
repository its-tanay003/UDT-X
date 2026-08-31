"""UDT-X Dynamic Risk Scoring Calculator (Phase 10).

Computes composite risk scores (0-100) combining:
1. Detection confidence (0.0 to 1.0)
2. Behavioral deviation magnitude (Phase 6 baseline Z-score)
3. Forensic evidence strength (quantity & quality of evidence items)
4. Incident correlation status (isolated alert vs multi-stage attack chain)
5. Asset Criticality Weight (configurable tier 1 to 5 per IP / subnet)
"""

from __future__ import annotations

import logging
from typing import Any

from baseline.client import get_baseline
from correlation.models import AttackChainProgression, Incident
from schema.models import Alert

logger = logging.getLogger("udtx.risk_engine.calculator")


class AssetCriticalityRegistry:
    """Maintains asset criticality weighting tiers (1.0 to 2.5 multiplier)."""

    DEFAULT_CRITICALITY = 1.0

    def __init__(
        self,
        asset_criticality_map: dict[str, float] | None = None,
    ) -> None:
        # Default high-value critical assets
        self.criticality_map: dict[str, float] = asset_criticality_map or {
            "10.0.0.1": 2.5,  # Domain Controller / Identity Provider
            "10.0.0.2": 2.2,  # Primary Database Cluster
            "10.0.0.5": 2.0,  # Core Production API Gateway
            "192.168.1.1": 1.8,  # Enterprise Perimeter Firewall / Router
        }

    def get_criticality(self, ip: str) -> float:
        """Fetch criticality multiplier for given IP."""
        return self.criticality_map.get(ip, self.DEFAULT_CRITICALITY)


class RiskEngineCalculator:
    """Computes multidimensional 0-100 Risk Scores for Alerts and Incidents."""

    def __init__(
        self,
        asset_registry: AssetCriticalityRegistry | None = None,
    ) -> None:
        self.asset_registry = asset_registry or AssetCriticalityRegistry()

    def calculate_alert_risk(
        self,
        alert: Alert,
        incident: Incident | None = None,
        redis_client: Any | None = None,
    ) -> float:
        """Calculate weighted composite risk score (0-100) for an alert."""
        # 1. Detection confidence contribution (Weight: 25%)
        conf_score = alert.confidence * 100.0

        # 2. Behavioral deviation magnitude from Phase 6 baseline (Weight: 25%)
        baseline = get_baseline(alert.src_ip, redis_client=redis_client)
        z_evidence = 0.0
        for ev in alert.evidence:
            if "zscore" in ev.key.lower() or "deviation" in ev.key.lower():
                try:
                    z_evidence = float(ev.value)
                except (ValueError, TypeError):
                    pass
        is_novel = not baseline.is_normal_destination(alert.dst_ip)
        deviation_score = min(
            100.0,
            max(z_evidence * 10.0, 30.0 if is_novel else 10.0),
        )

        # 3. Evidence strength contribution (Weight: 20%)
        evidence_count = len(alert.evidence)
        has_ioc = any(e.key == "IOC_MATCH" for e in alert.evidence)
        evidence_score = min(
            100.0,
            (evidence_count * 15.0) + (35.0 if has_ioc else 0.0),
        )

        # 4. Correlation Status (Weight: 15%)
        correlation_score = 20.0  # Default isolated
        if incident is not None:
            if incident.attack_chain == AttackChainProgression.FULL_KILL_CHAIN:
                correlation_score = 100.0
            elif incident.attack_chain in (
                AttackChainProgression.RECON_TO_C2,
                AttackChainProgression.C2_TO_EXFIL,
            ):
                correlation_score = 80.0
            elif len(incident.alert_ids) > 1:
                correlation_score = 50.0

        # Base raw composite score (0-100)
        raw_composite = (
            (conf_score * 0.25)
            + (deviation_score * 0.25)
            + (evidence_score * 0.20)
            + (correlation_score * 0.15)
            + (20.0 * 0.15)  # Baseline threat floor
        )

        # 5. Asset Criticality Multiplier
        crit_src = self.asset_registry.get_criticality(alert.src_ip)
        crit_dst = self.asset_registry.get_criticality(alert.dst_ip)
        max_crit = max(crit_src, crit_dst)

        final_risk = min(100.0, max(0.0, raw_composite * (0.8 + 0.2 * max_crit)))
        return round(final_risk, 1)

    def calculate_incident_risk(self, incident: Incident) -> float:
        """Calculate composite risk score for a multi-alert Incident."""
        base_risk = incident.risk_score
        if incident.attack_chain == AttackChainProgression.FULL_KILL_CHAIN:
            base_risk = max(base_risk, 95.0)
        elif incident.attack_chain in (
            AttackChainProgression.RECON_TO_C2,
            AttackChainProgression.C2_TO_EXFIL,
        ):
            base_risk = max(base_risk, 85.0)
        elif len(incident.alert_ids) > 2:
            base_risk = max(base_risk, 75.0)

        # Asset criticality of affected host
        crit = self.asset_registry.get_criticality(incident.primary_host_ip)
        final_risk = min(100.0, base_risk * (0.9 + 0.1 * crit))
        return round(final_risk, 1)
