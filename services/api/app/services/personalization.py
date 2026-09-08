"""UDT-X Personalization & Next-Best Action Recommendation Engine.

Analyzes operator role, historical shift context, current threat level,
and active anomalies to generate contextual, role-appropriate recommendations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from alert_manager.store import global_alert_store


class CopilotRecommendation(BaseModel):
    id: str
    title: str
    reasoning: str
    target_route: str
    action_id: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    priority: str = "medium"  # "critical", "high", "medium", "info"
    badge: str = "RECOMMENDED"


class PersonalizationEngine:
    """Deterministic, lightweight ML/heuristic personalization model."""

    @staticmethod
    def get_personalized_recommendations(
        user_role: str,
        user_display_name: str,
        user_settings: Optional[Dict[str, Any]] = None,
        recent_route: Optional[str] = None,
    ) -> List[CopilotRecommendation]:
        recommendations: List[CopilotRecommendation] = []
        alerts = global_alert_store.get_alerts(limit=50)
        incidents = global_alert_store.get_incidents(limit=10)

        critical_alerts = [a for a in alerts if getattr(a, "severity", "") == "critical"]
        high_risk_incidents = [i for i in incidents if getattr(i, "risk_score", 0) >= 75]

        # 1. Critical Threat Triage Rule
        if high_risk_incidents:
            inc = high_risk_incidents[0]
            recommendations.append(
                CopilotRecommendation(
                    id="rec_triage_incident",
                    title=f"Investigate Escalated Kill-Chain ({inc.incident_id})",
                    reasoning=f"Neo4j correlation synthesized a high-risk multi-stage incident (Score: {inc.risk_score:.1f}) involving {len(inc.alert_ids)} member alerts.",
                    target_route=f"/incidents/{inc.incident_id}",
                    action_id="navigate_page",
                    action_params={"target_route": f"/incidents/{inc.incident_id}"},
                    priority="critical",
                    badge="CRITICAL INCIDENT",
                )
            )
        elif critical_alerts:
            alt = critical_alerts[0]
            recommendations.append(
                CopilotRecommendation(
                    id="rec_review_critical_alert",
                    title=f"Inspect Critical Anomaly ({alt.threat_class})",
                    reasoning=f"Alert {alt.alert_id} was flagged with critical severity from source {alt.src_ip}. Inspect signed TreeSHAP feature attributions.",
                    target_route=f"/alerts/{alt.alert_id}/evidence",
                    action_id="navigate_page",
                    action_params={"target_route": f"/alerts/{alt.alert_id}/evidence"},
                    priority="high",
                    badge="ANOMALY EVIDENCE",
                )
            )

        # 2. Role-based Guidance
        if user_role == "admin":
            recommendations.append(
                CopilotRecommendation(
                    id="rec_admin_user_audit",
                    title="Audit Station Operator Clearances",
                    reasoning="As Station Administrator, review user accounts and active analyst authentication tokens.",
                    target_route="/profile",
                    action_id="navigate_page",
                    action_params={"target_route": "/profile"},
                    priority="medium",
                    badge="ADMIN CLEARANCE",
                )
            )
        else:
            # Analyst routine suggestion
            recommendations.append(
                CopilotRecommendation(
                    id="rec_analyst_sonar_sweep",
                    title="Run Sonar Threat Distribution Sweep",
                    reasoning="Analyze MITRE technique distribution across current 24-hour shift sliding window.",
                    target_route="/threats",
                    action_id="navigate_page",
                    action_params={"target_route": "/threats"},
                    priority="medium",
                    badge="SHIFT ROUTINE",
                )
            )

        # 3. Simulation & Validation Guidance
        if len(alerts) == 0:
            recommendations.append(
                CopilotRecommendation(
                    id="rec_simulate_scenario",
                    title="Inject Synthetic Attack Simulation in Replay Lab",
                    reasoning="No live traffic anomalies detected. Validate detection engine heuristics using the physical-guarded Replay Lab.",
                    target_route="/replay",
                    action_id="trigger_replay_simulation",
                    action_params={"scenario": "full_kill_chain"},
                    priority="info",
                    badge="REPLAY LAB",
                )
            )
        else:
            recommendations.append(
                CopilotRecommendation(
                    id="rec_export_siem",
                    title="Export Scored Telemetry in ArcSight CEF Format",
                    reasoning="Batch export buffered anomalous flows for upstream SIEM correlation (Splunk / Sentinel).",
                    target_route="/alerts",
                    action_id="export_siem_telemetry",
                    action_params={"format": "cef"},
                    priority="info",
                    badge="SIEM EXPORT",
                )
            )

        return recommendations[:3]


personalization_engine = PersonalizationEngine()
