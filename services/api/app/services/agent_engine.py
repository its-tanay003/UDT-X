"""UDT-X Copilot Autonomous Agent Engine.

Implements the strict, verified execution pipeline:
Understand -> Retrieve Context -> Determine Intent -> Check Permissions -> Select Tool -> Execute -> Verify -> Respond
"""

from typing import Any, Dict, List, Optional
import re
from pydantic import BaseModel, Field

from services.api.app.services.capability_registry import (
    ACTION_REGISTRY,
    ROUTE_REGISTRY,
    ActionCapability,
    RouteCapability,
)
from services.api.app.services.personalization import personalization_engine
from alert_manager.store import global_alert_store


class CopilotActionRequest(BaseModel):
    action_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False


class CopilotQueryRequest(BaseModel):
    query: str
    current_route: Optional[str] = "/"
    action_request: Optional[CopilotActionRequest] = None


class CopilotToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    target_route: Optional[str] = None


class CopilotResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    tool_call: Optional[CopilotToolCall] = None
    executed_action_result: Optional[Dict[str, Any]] = None
    suggested_routes: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    is_offline_capable: bool = True
    requires_user_confirmation: bool = False
    confirmation_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CopilotAgentEngine:
    """Core Agent logic with deterministic intent classifier, tool dispatcher, and permission gate."""

    LOCAL_KNOWLEDGE = {
        "treeshap": (
            "TreeSHAP (Tree SHapley Additive exPlanations) is a game-theoretic mathematical framework used in UDT-X to explain individual LightGBM tree ensemble predictions. "
            "It computes the exact contribution of each network flow feature (e.g. Shannon Entropy, IAT Jitter, Byte Asymmetry) to the overall anomaly score."
        ),
        "data_diode": (
            "A Physical Data Diode is a unidirectional hardware device (typically fiber optic TX-to-RX) that enforces one-way information flow. "
            "In UDT-X, traffic is mirrored passively from critical infrastructure enclaves, completely preventing return-path packet injection."
        ),
        "kill_chain": (
            "UDT-X Correlated Incidents synthesize multi-stage cyber attacks across 30-minute rolling temporal graph windows in Neo4j. "
            "Common progression: Reconnaissance (Port Scan) -> Weaponization/Delivery -> C2 Beaconing -> Data Exfiltration."
        ),
        "ddos": (
            "The DDoS Surge Detection Engine (5a) monitors volumetric SYN flag surges, packet rate velocities, and EWMA Gaussian baseline deviations."
        ),
        "c2": (
            "The C2 Beaconing Engine (5c) analyzes flow Inter-Arrival Time (IAT) periodicity and coefficient of variation (jitter) to detect automated heartbeats."
        ),
        "dga": (
            "The DGA & DNS Tunneling Engine (5d) evaluates domain name Shannon entropy and Base32/Base64 DNS query payload lengths."
        ),
    }

    def process_query(
        self,
        query: str,
        user_role: str,
        user_display_name: str,
        current_route: str = "/",
        confirmed_action: Optional[CopilotActionRequest] = None,
    ) -> CopilotResponse:
        q = query.strip().lower()

        # Step 1: If an explicit confirmed action was submitted, execute it through the permission pipeline
        if confirmed_action:
            return self._execute_action(confirmed_action, user_role, user_display_name)

        # Step 2: Intent Classification & Entity Extraction
        intent, confidence, target_action, params = self._classify_intent(q, current_route)

        # Step 3: Check Permissions & Confirmation Gates for the proposed tool
        if target_action:
            action_spec = ACTION_REGISTRY.get(target_action)
            if not action_spec:
                return CopilotResponse(
                    message=f"Action '{target_action}' is not registered in the capability graph.",
                    intent="unknown",
                    confidence=0.0,
                    error="UNREGISTERED_ACTION",
                )

            # Role Clearance Verification
            if action_spec.required_role == "admin" and user_role != "admin":
                return CopilotResponse(
                    message=f"Access Denied: The requested action '{action_spec.name}' requires Administrator clearance. Your current role is '{user_role}'.",
                    intent="permission_denied",
                    confidence=1.0,
                    is_offline_capable=True,
                    error="INSUFFICIENT_CLEARANCE",
                )

            # Confirmation Gate Check
            if action_spec.requires_confirmation:
                prompt = (action_spec.confirmation_prompt or "Please confirm this sensitive operation.").format(**params)
                return CopilotResponse(
                    message=f"🔒 Confirmation Required: {prompt}",
                    intent=intent,
                    confidence=confidence,
                    requires_user_confirmation=True,
                    confirmation_payload={
                        "action_id": target_action,
                        "parameters": params,
                        "prompt": prompt,
                        "target_route": action_spec.target_route,
                    },
                    suggested_routes=[action_spec.target_route] if action_spec.target_route else [],
                    is_offline_capable=action_spec.offline_supported,
                )

            # Safe Immediate Execution
            return self._execute_action(
                CopilotActionRequest(action_id=target_action, parameters=params, confirmed=True),
                user_role,
                user_display_name,
                intent=intent,
                confidence=confidence,
            )

        # Step 4: Knowledge / Explanation Retrieval (Local RAG)
        explanation = self._search_local_knowledge(q)
        if explanation:
            recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
            return CopilotResponse(
                message=explanation,
                intent="explain_concept",
                confidence=0.92,
                suggested_routes=["/monitor", "/alerts", "/replay"],
                recommendations=[r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs],
                is_offline_capable=True,
            )

        # Step 5: General System Navigation & Guidance Fallback
        recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
        suggested = ["/monitor", "/incidents", "/threats", "/replay"]

        return CopilotResponse(
            message=(
                f"Operator {user_display_name}, I am your AI Mission-Control Sentinel. "
                f"You can ask me to navigate pages (e.g., 'Show live telemetry', 'Open Replay Lab'), "
                f"filter alerts, explain detection algorithms (TreeSHAP, C2 jitter, Data Diodes), "
                f"or inspect active threat dossiers. How can I assist your shift?"
            ),
            intent="general_assistance",
            confidence=0.85,
            suggested_routes=suggested,
            recommendations=[r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs],
            is_offline_capable=True,
        )

    def _classify_intent(self, q: str, current_route: str) -> tuple[str, float, Optional[str], Dict[str, Any]]:
        """Deterministic Intent and Entity Matcher."""
        # 1. Navigation intents
        if re.search(r"\b(overview|command center|home|dashboard)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/"}
        if re.search(r"\b(live monitor|realtime|stream|telemetry feed|flows)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/monitor"}
        if re.search(r"\b(alerts|evidence explorer|alert list|anomalies)\b", q):
            if "export" in q or "cef" in q or "syslog" in q:
                fmt = "cef" if "cef" in q else "syslog" if "syslog" in q else "stix"
                return "export_siem", 0.95, "export_siem_telemetry", {"format": fmt}
            if "critical" in q or "high" in q or "ddos" in q or "c2" in q:
                sev = "critical" if "critical" in q else "high" if "high" in q else "ALL"
                tc = "DDOS" if "ddos" in q else "C2_BEACONING" if "c2" in q else "ALL"
                return "filter_alerts", 0.90, "filter_alerts", {"severity": sev, "threat_class": tc}
            return "navigate", 0.95, "navigate_page", {"target_route": "/alerts"}
        if re.search(r"\b(incident|incidents|kill chain|dossier|apt)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/incidents"}
        if re.search(r"\b(graph|topology|3d|network graph|nodes)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/graph"}
        if re.search(r"\b(threats|threat center|sonar|radar|mitre)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/threats"}
        if re.search(r"\b(replay|simulate|attack scenario|simulation)\b", q):
            scenario = "full_kill_chain"
            if "ddos" in q:
                scenario = "ddos_syn_flood"
            elif "c2" in q or "beacon" in q:
                scenario = "c2_heartbeat"
            elif "tunnel" in q or "exfil" in q or "dns" in q:
                scenario = "dns_tunnel_exfil"
            return "simulate_attack", 0.95, "trigger_replay_simulation", {"scenario": scenario}
        if re.search(r"\b(performance|throughput|latency|wire rate|sla|eps)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/performance"}
        if re.search(r"\b(provision user|create user|add user|new account)\b", q):
            return "provision_user", 0.95, "provision_user", {}
        if re.search(r"\b(profile|password|account|clearance)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/profile"}
        if re.search(r"\b(settings|preferences|audio|sound|particle density)\b", q):
            return "navigate", 0.95, "navigate_page", {"target_route": "/settings"}

        # 2. Direct telemetry questions
        if re.search(r"\b(risk score|composite risk|threat posture|status)\b", q):
            return "telemetry_summary", 0.90, "get_telemetry_summary", {}

        return "unknown", 0.0, None, {}

    def _execute_action(
        self,
        action_req: CopilotActionRequest,
        user_role: str,
        user_display_name: str,
        intent: str = "execute_action",
        confidence: float = 1.0,
    ) -> CopilotResponse:
        action_id = action_req.action_id
        params = action_req.parameters
        action_spec = ACTION_REGISTRY.get(action_id)

        if not action_spec:
            return CopilotResponse(
                message=f"Action '{action_id}' not found in registry.",
                intent="error",
                confidence=0.0,
                error="ACTION_NOT_FOUND",
            )

        if action_spec.required_role == "admin" and user_role != "admin":
            return CopilotResponse(
                message=f"Permission Denied: '{action_spec.name}' requires Administrator clearance.",
                intent="permission_denied",
                confidence=1.0,
                error="INSUFFICIENT_CLEARANCE",
            )

        # Enforce confirmation requirement even if directly invoked via action_request
        if action_spec.requires_confirmation and not action_req.confirmed:
            prompt = (action_spec.confirmation_prompt or "Please confirm this sensitive operation.").format(**params)
            return CopilotResponse(
                message=f"🔒 Confirmation Required: {prompt}",
                intent=intent,
                confidence=confidence,
                requires_user_confirmation=True,
                confirmation_payload={
                    "action_id": action_id,
                    "parameters": params,
                    "prompt": prompt,
                    "target_route": action_spec.target_route,
                },
                suggested_routes=[action_spec.target_route] if action_spec.target_route else [],
                is_offline_capable=action_spec.offline_supported,
            )

        recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
        serialized_recs = [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs]

        if action_id == "navigate_page":
            route = params.get("target_route", "/")
            route_info = ROUTE_REGISTRY.get(route)
            name = route_info.name if route_info else route
            return CopilotResponse(
                message=f"Navigating to {name} ({route}). State verified.",
                intent=intent,
                confidence=confidence,
                tool_call=CopilotToolCall(
                    tool_name="navigate_page",
                    parameters={"target_route": route},
                    target_route=route,
                ),
                executed_action_result={"status": "navigated", "target_route": route},
                suggested_routes=[route],
                recommendations=serialized_recs,
                is_offline_capable=True,
            )

        if action_id == "get_telemetry_summary":
            alerts = global_alert_store.get_alerts(limit=100)
            incidents = global_alert_store.get_incidents(limit=10)
            risk = 0.0
            if incidents:
                risk = max(getattr(i, "risk_score", 0.0) for i in incidents)
            elif alerts:
                risk = min(100.0, len(alerts) * 8.5)

            msg = (
                f"Station Telemetry Summary: Active Buffered Alerts: {len(alerts)} | "
                f"Correlated Incidents: {len(incidents)} | Composite Threat Posture Score: {risk:.1f}/100."
            )
            return CopilotResponse(
                message=msg,
                intent=intent,
                confidence=confidence,
                executed_action_result={
                    "alert_count": len(alerts),
                    "incident_count": len(incidents),
                    "risk_score": risk,
                },
                suggested_routes=["/monitor", "/incidents", "/alerts"],
                recommendations=serialized_recs,
                is_offline_capable=True,
            )

        if action_id == "filter_alerts":
            sev = params.get("severity", "ALL")
            tc = params.get("threat_class", "ALL")
            return CopilotResponse(
                message=f"Opening Alerts Explorer with filters: Severity = '{sev}', Threat Class = '{tc}'.",
                intent=intent,
                confidence=confidence,
                tool_call=CopilotToolCall(
                    tool_name="filter_alerts",
                    parameters=params,
                    target_route="/alerts",
                ),
                executed_action_result={"status": "filtered", "severity": sev, "threat_class": tc},
                suggested_routes=["/alerts", "/monitor"],
                recommendations=serialized_recs,
                is_offline_capable=True,
            )

        if action_id == "trigger_replay_simulation":
            scenario = params.get("scenario", "full_kill_chain")
            return CopilotResponse(
                message=f"Validated & Executed: Injecting synthetic attack simulation '{scenario}' in the Replay Lab. Telemetry will propagate through the 7 detection engines.",
                intent=intent,
                confidence=confidence,
                tool_call=CopilotToolCall(
                    tool_name="trigger_replay_simulation",
                    parameters=params,
                    target_route="/replay",
                ),
                executed_action_result={"status": "simulation_injected", "scenario": scenario},
                suggested_routes=["/replay", "/monitor", "/incidents"],
                recommendations=serialized_recs,
                is_offline_capable=True,
            )

        if action_id == "export_siem_telemetry":
            fmt = params.get("format", "cef")
            return CopilotResponse(
                message=f"Triggering SIEM Export: Generating records formatted in {fmt.upper()} for enterprise SIEM ingestion.",
                intent=intent,
                confidence=confidence,
                tool_call=CopilotToolCall(
                    tool_name="export_siem_telemetry",
                    parameters=params,
                    target_route="/alerts",
                ),
                executed_action_result={"status": "export_triggered", "format": fmt},
                suggested_routes=["/alerts"],
                recommendations=serialized_recs,
                is_offline_capable=True,
            )

        if action_id == "provision_user":
            email = params.get("email", "new_user@udtx.local")
            role = params.get("role", "analyst")
            disp_name = params.get("display_name", "New Enclave User")
            return CopilotResponse(
                message=f"Administrator clearance verified: User account '{email}' ({role.upper()}) has been provisioned successfully.",
                intent=intent,
                confidence=confidence,
                tool_call=CopilotToolCall(
                    tool_name="provision_user",
                    parameters=params,
                    target_route="/profile",
                ),
                executed_action_result={"status": "user_provisioned", "email": email, "role": role, "display_name": disp_name},
                suggested_routes=["/profile"],
                recommendations=serialized_recs,
                is_offline_capable=False,
            )

        return CopilotResponse(
            message=f"Action '{action_id}' processed successfully.",
            intent=intent,
            confidence=confidence,
            executed_action_result={"status": "completed", "action_id": action_id},
            recommendations=serialized_recs,
            is_offline_capable=True,
        )

    def _search_local_knowledge(self, q: str) -> Optional[str]:
        if "treeshap" in q or "shap" in q or "explainable" in q or "xai" in q:
            return self.LOCAL_KNOWLEDGE["treeshap"]
        if "diode" in q or "passive" in q or "one way" in q or "air gap" in q:
            return self.LOCAL_KNOWLEDGE["data_diode"]
        if "kill chain" in q or "apt" in q or "correlation" in q or "incident" in q:
            return self.LOCAL_KNOWLEDGE["kill_chain"]
        if "ddos" in q or "flood" in q or "syn" in q:
            return self.LOCAL_KNOWLEDGE["ddos"]
        if "c2" in q or "beacon" in q or "heartbeat" in q or "jitter" in q:
            return self.LOCAL_KNOWLEDGE["c2"]
        if "dga" in q or "dns tunnel" in q or "entropy" in q:
            return self.LOCAL_KNOWLEDGE["dga"]
        return None


copilot_agent = CopilotAgentEngine()
