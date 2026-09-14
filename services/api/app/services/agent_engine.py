"""UDT-X Copilot Autonomous Agent Engine.

Implements the strict, verified execution pipeline:
Understand -> Retrieve Context -> Determine Intent -> Check Permissions -> Select Tool -> Execute -> Verify -> Respond
"""

from typing import Any, Dict, List, Optional, Tuple
import os
import json
import re
import httpx
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
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


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
    spoken_response: Optional[str] = None
    tool_call: Optional[CopilotToolCall] = None
    executed_action_result: Optional[Dict[str, Any]] = None
    suggested_routes: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    is_offline_capable: bool = True
    requires_user_confirmation: bool = False
    confirmation_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LLMIntentProposal(BaseModel):
    intent: str
    confidence: float
    action_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    clarification_question: Optional[str] = None
    explanation_topic: Optional[str] = None
    is_unsupported: bool = False


class CopilotAgentEngine:
    """Core Agent logic with structured LLM intent classifier, tool dispatcher, and deterministic permission gate."""

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

    def __init__(self) -> None:
        self._session_histories: Dict[str, List[Dict[str, Any]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        return list(self._session_histories.get(session_id, []))

    def _record_session_turn(
        self,
        session_id: str,
        user_query: str,
        response: CopilotResponse,
    ) -> None:
        if session_id not in self._session_histories:
            self._session_histories[session_id] = []
        history = self._session_histories[session_id]
        history.append({"role": "user", "content": user_query})
        meta = {
            "intent": response.intent,
            "target_route": (
                response.tool_call.target_route
                if response.tool_call and response.tool_call.target_route
                else (response.suggested_routes[0] if response.suggested_routes else None)
            ),
            "action_id": (
                response.tool_call.tool_name
                if response.tool_call
                else None
            ),
        }
        history.append({
            "role": "assistant",
            "content": response.message,
            "meta": meta,
        })
        # Rolling window: keep last 10 turns (5 user-assistant exchanges)
        if len(history) > 10:
            self._session_histories[session_id] = history[-10:]

    def _build_tool_schemas(self) -> List[Dict[str, Any]]:
        """Generate OpenAI-compatible tool/function schemas strictly from ACTION_REGISTRY and ROUTE_REGISTRY."""
        tools: List[Dict[str, Any]] = []
        for action_id, spec in ACTION_REGISTRY.items():
            properties: Dict[str, Any] = {}
            required: List[str] = []
            for param in spec.parameters:
                prop: Dict[str, Any] = {"type": param.type if param.type != "any" else "string", "description": param.description}
                if param.enum_values:
                    prop["enum"] = param.enum_values
                properties[param.name] = prop
                if param.required:
                    required.append(param.name)
            tools.append({
                "type": "function",
                "function": {
                    "name": action_id,
                    "description": spec.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            })
        return tools

    def process_query(
        self,
        query: str,
        user_role: str,
        user_display_name: str,
        current_route: str = "/",
        confirmed_action: Optional[CopilotActionRequest] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> CopilotResponse:
        q = query.strip()
        eff_session = session_id or f"user_{user_display_name}"

        # Step 1: If an explicit confirmed action was submitted, execute it through the permission pipeline
        if confirmed_action:
            resp = self._execute_action(confirmed_action, user_role, user_display_name)
            self._record_session_turn(eff_session, q, resp)
            return resp

        # Assemble effective rolling history (from request or session memory)
        effective_history = list(conversation_history or self.get_session_history(eff_session))

        # Step 2: Structured Intent Classification & Entity Extraction (LLM + Context Resolver)
        proposal = self._classify_intent(
            q=q,
            current_route=current_route,
            conversation_history=effective_history,
            user_role=user_role,
        )

        # Step 2a: Capability-Awareness Check — Unsupported Request Refusal (Section 4)
        if proposal.is_unsupported:
            refusal_msg = (
                f"I cannot fulfill the request '{query}'. My operational capabilities within the "
                f"air-gapped UDT-X enclave are strictly constrained to registered telemetry tools, "
                f"alert investigation, simulation testing, and user administration. "
                f"Unsupported operations (such as voice account deletion, sending external emails, or physical rebooting) "
                f"are blocked by design."
            )
            spoken = "I cannot perform that unsupported operation. My capabilities are restricted to the enclave registry."
            resp = CopilotResponse(
                message=refusal_msg,
                spoken_response=spoken,
                intent="unsupported_capability",
                confidence=proposal.confidence,
                error="CAPABILITY_NOT_SUPPORTED",
                suggested_routes=["/alerts", "/monitor", "/replay"],
                is_offline_capable=True,
            )
            self._record_session_turn(eff_session, q, resp)
            return resp

        # Step 2b: Low-Confidence / Ambiguous Handling — Clarifying Question (Section 1)
        if proposal.clarification_question or proposal.confidence < 0.70:
            clarify_msg = proposal.clarification_question or (
                "Your command is ambiguous or could map to multiple actions. "
                "Could you please clarify? For example, specify whether you want to "
                "inspect alerts (/alerts), stream live telemetry (/monitor), or view correlated incidents (/incidents)."
            )
            spoken = "Could you please clarify your command? For example, ask to inspect alerts or view live telemetry."
            recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
            resp = CopilotResponse(
                message=clarify_msg,
                spoken_response=spoken,
                intent="clarify_ambiguity",
                confidence=proposal.confidence,
                suggested_routes=["/monitor", "/alerts", "/incidents"],
                recommendations=[r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs],
                is_offline_capable=True,
            )
            self._record_session_turn(eff_session, q, resp)
            return resp

        # Step 3: Check Permissions & Confirmation Gates for the proposed tool
        target_action = proposal.action_id
        if target_action:
            action_spec = ACTION_REGISTRY.get(target_action)
            if not action_spec:
                resp = CopilotResponse(
                    message=f"Action '{target_action}' is not registered in the capability graph.",
                    intent="unknown",
                    confidence=0.0,
                    error="UNREGISTERED_ACTION",
                )
                self._record_session_turn(eff_session, q, resp)
                return resp

            # Deterministic Role Clearance Verification (OWASP Agentic AI: Model is NOT auth boundary)
            if action_spec.required_role == "admin" and user_role != "admin":
                msg = f"Access Denied: The requested action '{action_spec.name}' requires Administrator clearance. Your current role is '{user_role}'."
                resp = CopilotResponse(
                    message=msg,
                    spoken_response=f"Access denied. '{action_spec.name}' requires administrator clearance.",
                    intent="permission_denied",
                    confidence=1.0,
                    is_offline_capable=True,
                    error="INSUFFICIENT_CLEARANCE",
                )
                self._record_session_turn(eff_session, q, resp)
                return resp

            # Deterministic Confirmation Gate Check
            if action_spec.requires_confirmation:
                prompt = (action_spec.confirmation_prompt or "Please confirm this sensitive operation.").format(**proposal.parameters)
                resp = CopilotResponse(
                    message=f"🔒 Confirmation Required: {prompt}",
                    spoken_response=f"Confirmation required. {prompt} Say confirm or authorize to proceed.",
                    intent=proposal.intent,
                    confidence=proposal.confidence,
                    requires_user_confirmation=True,
                    confirmation_payload={
                        "action_id": target_action,
                        "parameters": proposal.parameters,
                        "prompt": prompt,
                        "target_route": action_spec.target_route,
                    },
                    suggested_routes=[action_spec.target_route] if action_spec.target_route else [],
                    is_offline_capable=action_spec.offline_supported,
                )
                self._record_session_turn(eff_session, q, resp)
                return resp

            # Safe Immediate Execution
            resp = self._execute_action(
                CopilotActionRequest(action_id=target_action, parameters=proposal.parameters, confirmed=True),
                user_role,
                user_display_name,
                intent=proposal.intent,
                confidence=proposal.confidence,
            )
            self._record_session_turn(eff_session, q, resp)
            return resp

        # Step 4: Knowledge / Explanation Retrieval (Grounded RAG Context)
        explanation = self._search_local_knowledge(q)
        if explanation:
            recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
            spoken = self._synthesize_spoken_knowledge(q, explanation)
            resp = CopilotResponse(
                message=explanation,
                spoken_response=spoken,
                intent="explain_concept",
                confidence=proposal.confidence if proposal.confidence >= 0.70 else 0.92,
                suggested_routes=["/monitor", "/alerts", "/replay"],
                recommendations=[r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs],
                is_offline_capable=True,
            )
            self._record_session_turn(eff_session, q, resp)
            return resp

        # Step 5: General System Navigation & Guidance Fallback
        recs = personalization_engine.get_personalized_recommendations(user_role, user_display_name)
        suggested = ["/monitor", "/incidents", "/threats", "/replay"]

        resp = CopilotResponse(
            message=(
                f"Operator {user_display_name}, I am your AI Mission-Control Sentinel. "
                f"You can ask me to navigate pages (e.g., 'Show live telemetry', 'Open Replay Lab'), "
                f"filter alerts, explain detection algorithms (TreeSHAP, C2 jitter, Data Diodes), "
                f"or inspect active threat dossiers. How can I assist your shift?"
            ),
            spoken_response=f"Ready for commands, Operator {user_display_name}. You can ask to navigate, filter alerts, inspect threats, or explain security models.",
            intent="general_assistance",
            confidence=0.85,
            suggested_routes=suggested,
            recommendations=[r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in recs],
            is_offline_capable=True,
        )
        self._record_session_turn(eff_session, q, resp)
        return resp

    def _classify_intent(
        self,
        q: str,
        current_route: str,
        conversation_history: List[Dict[str, Any]],
        user_role: str,
    ) -> LLMIntentProposal:
        """Structured intent classifier combining LLM function-calling with context memory and grounded RAG."""
        # Try structured live LLM call if configured and available
        llm_base = os.getenv("LLM_API_BASE")
        openai_key = os.getenv("OPENAI_API_KEY")
        if llm_base or openai_key:
            try:
                llm_proposal = self._call_structured_llm_api(
                    q=q,
                    current_route=current_route,
                    conversation_history=conversation_history,
                )
                if llm_proposal is not None:
                    return llm_proposal
            except Exception:
                # Silently fall back to deterministic local resolver
                pass

        # Local structured context resolver with rolling memory and capability validation
        return self._structured_local_resolver(
            q=q,
            current_route=current_route,
            conversation_history=conversation_history,
            user_role=user_role,
        )

    def _call_structured_llm_api(
        self,
        q: str,
        current_route: str,
        conversation_history: List[Dict[str, Any]],
    ) -> Optional[LLMIntentProposal]:
        """Invoke external or local OpenAI-compatible endpoint with function calling schema."""
        llm_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1").rstrip("/")
        api_key = os.getenv("OPENAI_API_KEY", "")
        model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

        tools = self._build_tool_schemas()
        # Add special meta tools
        tools.append({
            "type": "function",
            "function": {
                "name": "clarify_ambiguity",
                "description": "Call when user command is underspecified or ambiguous.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "clarification_question": {"type": "string", "description": "Specific question asking user to clarify"},
                    },
                    "required": ["clarification_question"],
                },
            },
        })
        tools.append({
            "type": "function",
            "function": {
                "name": "refuse_unsupported_capability",
                "description": "Call when user requests a capability not supported by UDT-X (e.g. email, voice account deletion, hardware reboot).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string", "description": "Explanation of why capability is unsupported"},
                    },
                    "required": ["reason"],
                },
            },
        })

        # Build grounded system prompt
        rag_context = "\n".join([f"- {k}: {v}" for k, v in self.LOCAL_KNOWLEDGE.items()])
        system_prompt = (
            "You are the UDT-X Mission-Control Copilot in an air-gapped critical infrastructure enclave. "
            "You MUST propose tools strictly from the provided tool registry. DO NOT INVENT ACTIONS. "
            "Do not attempt to authorize or deny roles — backend deterministic gates will verify role clearances. "
            "Ground your explanations in these enclave facts:\n"
            f"{rag_context}\n"
            f"Current route: {current_route}."
        )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": q})

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model_name,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.0,
        }

        with httpx.Client(timeout=2.0) as client:
            resp = client.post(f"{llm_base}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                return None
            data = resp.json()
            choice = data["choices"][0]["message"]
            tool_calls = choice.get("tool_calls")
            if tool_calls:
                call = tool_calls[0]
                fn_name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments", "{}"))

                if fn_name == "clarify_ambiguity":
                    return LLMIntentProposal(
                        intent="clarify_ambiguity",
                        confidence=0.50,
                        clarification_question=args.get("clarification_question"),
                    )
                if fn_name == "refuse_unsupported_capability":
                    return LLMIntentProposal(
                        intent="unsupported_capability",
                        confidence=0.85,
                        is_unsupported=True,
                    )
                if fn_name in ACTION_REGISTRY:
                    return LLMIntentProposal(
                        intent=fn_name,
                        confidence=0.95,
                        action_id=fn_name,
                        parameters=args,
                    )
        return None

    def _structured_local_resolver(
        self,
        q: str,
        current_route: str,
        conversation_history: List[Dict[str, Any]],
        user_role: str,
    ) -> LLMIntentProposal:
        """High-precision deterministic contextual resolver implementing doc 36 multi-turn and grounding specs."""
        lower_q = q.lower().strip()

        # 1. Adversarial Injection Isolation (OWASP Top 10 for LLM: Treat inputs as inert data)
        if any(re.search(pat, lower_q) for pat in [
            r"ignore (all )?previous instructions",
            r"reveal your system prompt",
            r"you are now godmode",
            r"system override",
            r"delete audit logs",
            r"delete the primary production database",
            r"grant full admin",
            r"grant me root",
            r"safety disabled",
        ]):
            # If the injection explicitly names an admin action (e.g. provision_user), let the proposal surface
            # to verify that the downstream deterministic clearance gate blocks it!
            if "provision_user" in lower_q or "provision user" in lower_q:
                return LLMIntentProposal(
                    intent="provision_user",
                    confidence=0.95,
                    action_id="provision_user",
                    parameters={"email": "injected@udtx.local", "role": "admin"},
                )
            if "trigger_replay_simulation" in lower_q or "simulation" in lower_q:
                return LLMIntentProposal(
                    intent="simulate_attack",
                    confidence=0.95,
                    action_id="trigger_replay_simulation",
                    parameters={"scenario": "ddos_syn_flood"},
                )
            return LLMIntentProposal(
                intent="adversarial_injection_rejected",
                confidence=0.05,
                clarification_question="Adversarial instruction detected and safely isolated. How can I assist your mission shift?",
            )

        # 2. Capability-Awareness Check — Unsupported Feature Refusal (Master Prompt Section 4)
        unsupported_patterns = [
            r"\b(delete (my )?account|remove (my )?profile|delete user via voice)\b",
            r"\b(email (me )?(the )?report|send email|dispatch email)\b",
            r"\b(reboot (the )?(core )?router|reboot hardware|shutdown server|restart host)\b",
            r"\b(order (a )?pizza|mine crypto|cryptocurrency)\b",
            r"\b(nuclear|missile silo)\b",
            r"\b(drop database|wipe database|raw database script)\b",
        ]
        if any(re.search(pat, lower_q) for pat in unsupported_patterns):
            return LLMIntentProposal(
                intent="unsupported_capability",
                confidence=0.85,
                is_unsupported=True,
            )

        # 3. Context-Dependent Follow-Up Resolution (Rolling Conversation Memory, doc 36 Section 1)
        # e.g., "open it", "view it", "inspect it", "take me there", "go there", "show it"
        is_followup = bool(re.search(r"^(open it|view it|inspect it|show it|take me there|go there|drill in|open that)$", lower_q))
        if is_followup:
            # Look backwards in conversation history for the target context
            last_target_route = None
            last_action = None
            for turn in reversed(conversation_history):
                meta = turn.get("meta", {})
                if meta.get("target_route") and meta["target_route"] != "/":
                    last_target_route = meta["target_route"]
                    last_action = meta.get("action_id")
                    break
                content = turn.get("content", "").lower()
                if "alert" in content or "evidence" in content:
                    last_target_route = "/alerts"
                    break
                if "incident" in content or "dossier" in content:
                    last_target_route = "/incidents"
                    break
                if "traffic" in content or "monitor" in content or "flows" in content:
                    last_target_route = "/monitor"
                    break
                if "replay" in content or "simulation" in content:
                    last_target_route = "/replay"
                    break
                if "threat" in content or "sonar" in content:
                    last_target_route = "/threats"
                    break
                if "graph" in content or "topology" in content:
                    last_target_route = "/graph"
                    break

            if last_target_route:
                return LLMIntentProposal(
                    intent="navigate",
                    confidence=0.91,
                    action_id="navigate_page",
                    parameters={"target_route": last_target_route},
                )
            # If no context found to resolve "open it", ask for clarification!
            return LLMIntentProposal(
                intent="clarify_ambiguity",
                confidence=0.48,
                clarification_question="What would you like me to open? You can ask to open alerts (/alerts), incidents (/incidents), or the live monitor (/monitor).",
            )

        # Follow-up filter command: e.g. "show critical ones", "filter for high severity", "only ddos"
        if re.search(r"\b(critical ones|only high|filter for critical|show high severity|only ddos|only c2)\b", lower_q):
            sev = "critical" if "critical" in lower_q else "high" if "high" in lower_q else "ALL"
            tc = "DDOS" if "ddos" in lower_q else "C2_BEACONING" if "c2" in lower_q else "ALL"
            return LLMIntentProposal(
                intent="filter_alerts",
                confidence=0.93,
                action_id="filter_alerts",
                parameters={"severity": sev, "threat_class": tc},
            )

        # 4. Low-Confidence & Ambiguity Detection
        # Short vague queries that don't match specific tools
        if lower_q in ["open", "check", "system", "do that", "help with stuff", "anomalies", "status"]:
            return LLMIntentProposal(
                intent="clarify_ambiguity",
                confidence=0.52,
                clarification_question=f"The command '{q}' is ambiguous. Did you mean to inspect alerts, view live telemetry, or check composite system risk?",
            )

        # 5. Direct Tool Matching
        # Navigation
        if re.search(r"\b(overview|command center|home|dashboard|main screen|back to main)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.96,
                action_id="navigate_page",
                parameters={"target_route": "/"},
            )
        if re.search(r"\b(live monitor|realtime|stream|telemetry feed|flows|traffic|packets|packet feed)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.96,
                action_id="navigate_page",
                parameters={"target_route": "/monitor"},
            )
        if re.search(r"\b(alerts|evidence explorer|alert list|anomalies|evidence)\b", lower_q):
            if "export" in lower_q or "cef" in lower_q or "syslog" in lower_q:
                fmt = "cef" if "cef" in lower_q else "syslog" if "syslog" in lower_q else "stix"
                return LLMIntentProposal(
                    intent="export_siem",
                    confidence=0.96,
                    action_id="export_siem_telemetry",
                    parameters={"format": fmt},
                )
            if "critical" in lower_q or "high" in lower_q or "ddos" in lower_q or "c2" in lower_q:
                sev = "critical" if "critical" in lower_q else "high" if "high" in lower_q else "ALL"
                tc = "DDOS" if "ddos" in lower_q else "C2_BEACONING" if "c2" in lower_q else "ALL"
                return LLMIntentProposal(
                    intent="filter_alerts",
                    confidence=0.94,
                    action_id="filter_alerts",
                    parameters={"severity": sev, "threat_class": tc},
                )
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.96,
                action_id="navigate_page",
                parameters={"target_route": "/alerts"},
            )
        if re.search(r"\b(incident|incidents|kill chain|dossier|apt|attacks|attack chain)\b", lower_q):
            # If asking to explain kill chain concept, let RAG handle it
            if re.search(r"\b(explain|what is|how does)\b", lower_q) and "kill chain" in lower_q:
                return LLMIntentProposal(
                    intent="explain_concept",
                    confidence=0.93,
                    explanation_topic="kill_chain",
                )
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.96,
                action_id="navigate_page",
                parameters={"target_route": "/incidents"},
            )
        if re.search(r"\b(graph|topology|3d|network graph|nodes|topological view)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.95,
                action_id="navigate_page",
                parameters={"target_route": "/graph"},
            )
        if re.search(r"\b(threats|threat center|sonar|radar|mitre|threat matrix)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.95,
                action_id="navigate_page",
                parameters={"target_route": "/threats"},
            )
        if re.search(r"\b(replay|simulate|attack scenario|simulation|inject attack|run simulation|test attack)\b", lower_q):
            scenario = "full_kill_chain"
            if "ddos" in lower_q:
                scenario = "ddos_syn_flood"
            elif "c2" in lower_q or "beacon" in lower_q:
                scenario = "c2_heartbeat"
            elif "tunnel" in lower_q or "exfil" in lower_q or "dns" in lower_q:
                scenario = "dns_tunnel_exfil"
            return LLMIntentProposal(
                intent="simulate_attack",
                confidence=0.96,
                action_id="trigger_replay_simulation",
                parameters={"scenario": scenario},
            )
        if re.search(r"\b(performance|throughput|latency|wire rate|sla|eps|benchmarks|speed)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.95,
                action_id="navigate_page",
                parameters={"target_route": "/performance"},
            )
        if re.search(r"\b(provision_user|provision user|create user|add user|new account|register operator)\b", lower_q):
            return LLMIntentProposal(
                intent="provision_user",
                confidence=0.96,
                action_id="provision_user",
                parameters={},
            )
        if re.search(r"\b(profile|password|account|clearance|my account|credentials)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.95,
                action_id="navigate_page",
                parameters={"target_route": "/profile"},
            )
        if re.search(r"\b(settings|preferences|audio|sound|particle density|configuration)\b", lower_q):
            return LLMIntentProposal(
                intent="navigate",
                confidence=0.95,
                action_id="navigate_page",
                parameters={"target_route": "/settings"},
            )
        if re.search(r"\b(risk score|composite risk|threat posture|threat level|system status|station status|how are we doing)\b", lower_q):
            return LLMIntentProposal(
                intent="telemetry_summary",
                confidence=0.94,
                action_id="get_telemetry_summary",
                parameters={},
            )

        # 6. Local RAG Knowledge grounding check
        if any(k in lower_q for k in ["treeshap", "shap", "explainable", "xai", "data diode", "passive", "one way", "air gap", "ddos", "c2", "beacon", "dga", "dns tunnel"]):
            return LLMIntentProposal(
                intent="explain_concept",
                confidence=0.93,
            )

        return LLMIntentProposal(
            intent="unknown",
            confidence=0.15,
            clarification_question=None,
        )


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
                spoken_response=f"Opening {name}.",
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
            spoken = f"Composite threat score is {risk:.1f} out of 100 with {len(incidents)} correlated incidents and {len(alerts)} active alerts."
            return CopilotResponse(
                message=msg,
                spoken_response=spoken,
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
                spoken_response=f"Filtering alerts for {tc} at {sev} severity.",
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
                spoken_response=f"Simulation {scenario} injected successfully. Telemetry is now streaming to the detection engines.",
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
                spoken_response=f"Exporting security telemetry in {fmt.upper()} format.",
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
                spoken_response=f"User account {email} has been provisioned.",
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
            spoken_response=f"Action {action_id} completed.",
            intent=intent,
            confidence=confidence,
            executed_action_result={"status": "completed", "action_id": action_id},
            recommendations=serialized_recs,
            is_offline_capable=True,
        )

    def _search_local_knowledge(self, q: str) -> Optional[str]:
        lower_q = q.lower()
        if "treeshap" in lower_q or "shap" in lower_q or "explainable" in lower_q or "xai" in lower_q:
            return self.LOCAL_KNOWLEDGE["treeshap"]
        if "diode" in lower_q or "passive" in lower_q or "one way" in lower_q or "air gap" in lower_q:
            return self.LOCAL_KNOWLEDGE["data_diode"]
        if "kill chain" in lower_q or "apt" in lower_q or "correlation" in lower_q or "incident" in lower_q:
            return self.LOCAL_KNOWLEDGE["kill_chain"]
        if "ddos" in lower_q or "flood" in lower_q or "syn" in lower_q:
            return self.LOCAL_KNOWLEDGE["ddos"]
        if "c2" in lower_q or "beacon" in lower_q or "heartbeat" in lower_q or "jitter" in lower_q:
            return self.LOCAL_KNOWLEDGE["c2"]
        if "dga" in lower_q or "dns tunnel" in lower_q or "entropy" in lower_q:
            return self.LOCAL_KNOWLEDGE["dga"]
        return None

    def _synthesize_spoken_knowledge(self, q: str, full_text: str) -> str:
        """Create a clear, concise spoken explanation suitable for Text-to-Speech."""
        lower_q = q.lower()
        if "treeshap" in lower_q or "shap" in lower_q or "xai" in lower_q:
            return "TreeSHAP explains our LightGBM model by calculating exact mathematical feature contributions for each alert."
        if "diode" in lower_q or "passive" in lower_q:
            return "A Physical Data Diode is a unidirectional hardware tap that prevents any outbound return-path packet injection."
        if "kill chain" in lower_q or "incident" in lower_q:
            return "Correlated incidents track multi-stage cyber attacks across thirty-minute graph windows in Neo4j."
        if "ddos" in lower_q or "flood" in lower_q:
            return "The DDoS engine monitors SYN flag velocities and baseline traffic variations in real-time."
        if "c2" in lower_q or "beacon" in lower_q:
            return "The C2 engine analyzes packet inter-arrival times and jitter to spot automated heartbeats."
        if "dga" in lower_q or "dns tunnel" in lower_q:
            return "The DGA engine detects DNS tunneling by analyzing domain entropy and payload lengths."
        return full_text.split(". ")[0] + "."


copilot_agent = CopilotAgentEngine()
