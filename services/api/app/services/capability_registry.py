"""UDT-X Website Capability Graph & Action Registry.

Defines all available website routes, operations, tools, permission matrices,
confirmation gates, and offline execution capabilities.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParameterSpec(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None


class ActionCapability(BaseModel):
    action_id: str
    name: str
    description: str
    category: str  # "navigation", "telemetry", "forensics", "simulation", "settings", "admin"
    required_role: str = "analyst"  # "analyst" or "admin"
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    offline_supported: bool = True
    online_fallback_behavior: str = "execute"  # "execute", "stage_queue", "explain_unavailable"
    target_route: Optional[str] = None
    parameters: List[ParameterSpec] = Field(default_factory=list)


class RouteCapability(BaseModel):
    route: str
    name: str
    description: str
    min_role: str = "analyst"
    offline_supported: bool = True
    key_features: List[str]
    sample_queries: List[str]


# ---------------------------------------------------------------------------
# Structured Website Capability Registry
# ---------------------------------------------------------------------------

ROUTE_REGISTRY: Dict[str, RouteCapability] = {
    "/": RouteCapability(
        route="/",
        name="Security Command Center / Overview",
        description="Global enclave operational posture, ambient 3D Listening Sphere, composite threat risk ring, and hardware data diode status.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "3D Ambient Listening Sphere (WebGL passive diode)",
            "Composite Risk Dial (0-100 hazard score)",
            "4 Core Instrument KPI cards with live velocity count",
            "Detection & Inference Subsystem Reference Architecture",
        ],
        sample_queries=[
            "Take me to the overview",
            "What is our composite risk score?",
            "Show me the command center",
        ],
    ),
    "/monitor": RouteCapability(
        route="/monitor",
        name="Live Telemetry Monitor",
        description="Continuous zero-latency streaming table of inbound network flows and detected anomalies across the passive mirror tap.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Zero-refresh streaming table via WebSocket",
            "Severity & threat category filters",
            "Sub-second IP and hash search",
            "Quick-pivot links to explainable AI evidence",
        ],
        sample_queries=[
            "Show me the live monitor",
            "Filter for critical alerts in the live stream",
            "Are there any active DDoS anomalies streaming right now?",
        ],
    ),
    "/alerts": RouteCapability(
        route="/alerts",
        name="Alerts & Evidence Explorer Index",
        description="Comprehensive index of scored security alerts with MITRE ATT&CK technique tags and 1-click SIEM export.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "ArcSight CEF and RFC 5424 Syslog batch exporters",
            "Class and severity multi-parameter filters",
            "Staggered entrance table and mobile card view",
        ],
        sample_queries=[
            "Open the alerts list",
            "Export alerts to CEF",
            "Show all C2 beaconing alerts",
        ],
    ),
    "/incidents": RouteCapability(
        route="/incidents",
        name="Security Incidents Dossier Index",
        description="Chronological multi-stage attack chains synthesized across 30-minute rolling Neo4j graph windows.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Sortable incident cards by risk score, timestamp, and alert volume",
            "Correlated threat class tags",
            "Affected host and temporal window metadata",
        ],
        sample_queries=[
            "Show me all incidents",
            "What are the highest risk attack chains?",
            "List active APT incidents",
        ],
    ),
    "/graph": RouteCapability(
        route="/graph",
        name="3D Network Evidence Graph",
        description="Full-screen interactive 3D WebGL topological graph mapping communicating hosts and inbound data diode flows.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Interactive orbital camera with bloom post-processing",
            "Click-to-inspect host nodes",
            "Directional Bezier communication arcs",
        ],
        sample_queries=[
            "Open the 3D network graph",
            "Inspect the host topology",
            "Show communicating nodes",
        ],
    ),
    "/threats": RouteCapability(
        route="/threats",
        name="Threat Intelligence Center",
        description="Polar coordinate radar sweep visualization mapping threat distributions, MITRE matrices, and severity wedges.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "D3 polar sonar radar sweep",
            "Threat class distribution wedges",
            "Historical temporal filters (1h, 24h, 7d, 30d)",
        ],
        sample_queries=[
            "Show threat intelligence sonar",
            "What MITRE techniques are most active?",
            "Open the threat center",
        ],
    ),
    "/replay": RouteCapability(
        route="/replay",
        name="Deterministic Replay Lab",
        description="Hardware-isolated simulation console with physical-style toggle switches to inject synthetic attack scenarios safely.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Pre-configured attack templates (APT Kill-Chain, DDoS, DGA C2, Exfil)",
            "Safety interlock guard",
            "Synthetic packet stream injector",
        ],
        sample_queries=[
            "Go to Replay Lab",
            "Simulate a multi-stage APT attack",
            "Test detection engines with synthetic traffic",
        ],
    ),
    "/performance": RouteCapability(
        route="/performance",
        name="Performance & SLA Telemetry",
        description="System throughput benchmarks sustaining 124,850+ EPS with sub-5ms latency and zero packet loss.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Events Per Second wire rate meters",
            "P50, P95, P99 inference latency tracking",
            "Microservice memory and CPU utilization",
        ],
        sample_queries=[
            "What is our current wire rate?",
            "Show performance and latency metrics",
            "Check system SLA",
        ],
    ),
    "/profile": RouteCapability(
        route="/profile",
        name="Operator Profile & Identity",
        description="Analyst credential management, station password changes, and administrator user provisioning.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Callsign & display name updates",
            "Password changes with bcrypt verification",
            "Administrator user provisioning table",
        ],
        sample_queries=[
            "Open my profile",
            "Change my password",
            "Provision a new analyst account",
        ],
    ),
    "/settings": RouteCapability(
        route="/settings",
        name="Station Settings & Diagnostics",
        description="Audio alert toggles, 3D particle density tuning, default SIEM format, and station tour triggers.",
        min_role="analyst",
        offline_supported=True,
        key_features=[
            "Critical threat audio pings",
            "3D Listening Sphere GPU particle density selector",
            "Replay Station Tour & Reset Briefing actions",
        ],
        sample_queries=[
            "Open station settings",
            "Disable critical sound alerts",
            "Replay the onboarding tour",
        ],
    ),
}

ACTION_REGISTRY: Dict[str, ActionCapability] = {
    "navigate_page": ActionCapability(
        action_id="navigate_page",
        name="Navigate Website Page",
        description="Safely navigate the operator to any available console screen or dossier route.",
        category="navigation",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        parameters=[
            ParameterSpec(
                name="target_route",
                type="string",
                description="The destination path (e.g., '/monitor', '/alerts', '/replay', '/graph')",
                required=True,
            )
        ],
    ),
    "get_telemetry_summary": ActionCapability(
        action_id="get_telemetry_summary",
        name="Get Telemetry Summary",
        description="Retrieve current active anomaly counts, wire flow rate, and composite risk posture.",
        category="telemetry",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        parameters=[],
    ),
    "filter_alerts": ActionCapability(
        action_id="filter_alerts",
        name="Filter & Inspect Alerts",
        description="Filter buffered alerts by severity level or threat class and navigate to Alerts view.",
        category="forensics",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        target_route="/alerts",
        parameters=[
            ParameterSpec(
                name="severity",
                type="string",
                description="Alert severity level",
                required=False,
                enum_values=["critical", "high", "medium", "low", "ALL"],
            ),
            ParameterSpec(
                name="threat_class",
                type="string",
                description="Specific threat category",
                required=False,
                enum_values=["DDOS", "C2_BEACONING", "RECONNAISSANCE", "DGA", "DNS_TUNNELING", "EXFILTRATION", "ALL"],
            ),
        ],
    ),
    "trigger_replay_simulation": ActionCapability(
        action_id="trigger_replay_simulation",
        name="Trigger Attack Simulation",
        description="Inject a synthetic attack scenario into the detection pipeline within the isolated Replay Lab.",
        category="simulation",
        required_role="analyst",
        requires_confirmation=True,
        confirmation_prompt="Are you sure you want to inject a synthetic {scenario} scenario into the local detection pipeline?",
        offline_supported=True,
        target_route="/replay",
        parameters=[
            ParameterSpec(
                name="scenario",
                type="string",
                description="Attack simulation scenario type",
                required=True,
                default="full_kill_chain",
                enum_values=["full_kill_chain", "ddos_syn_flood", "c2_heartbeat", "dns_tunnel_exfil"],
            )
        ],
    ),
    "export_siem_telemetry": ActionCapability(
        action_id="export_siem_telemetry",
        name="Export SIEM Records",
        description="Trigger an immediate telemetry export formatted in ArcSight CEF or Syslog RFC 5424.",
        category="telemetry",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        target_route="/alerts",
        parameters=[
            ParameterSpec(
                name="format",
                type="string",
                description="Export format",
                required=True,
                default="cef",
                enum_values=["cef", "syslog", "stix"],
            )
        ],
    ),
    "update_station_setting": ActionCapability(
        action_id="update_station_setting",
        name="Update Station Setting",
        description="Modify station audio alerts, display density, or telemetry options.",
        category="settings",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        target_route="/settings",
        parameters=[
            ParameterSpec(name="category", type="string", description="Settings category ('alerting' | 'display' | 'data_export')", required=True),
            ParameterSpec(name="key", type="string", description="Setting key to update", required=True),
            ParameterSpec(name="value", type="any", description="New value for the setting", required=True),
        ],
    ),
    "provision_user": ActionCapability(
        action_id="provision_user",
        name="Provision New Analyst Account",
        description="Create a new operator identity in the air-gapped station database (Administrator only).",
        category="admin",
        required_role="admin",
        requires_confirmation=True,
        confirmation_prompt="Confirm provisioning new station user '{email}' with role '{role}'?",
        offline_supported=False,
        online_fallback_behavior="stage_queue",
        target_route="/profile",
        parameters=[
            ParameterSpec(name="email", type="string", description="User enclave email address", required=True),
            ParameterSpec(name="display_name", type="string", description="Display call-sign", required=True),
            ParameterSpec(name="password", type="string", description="Initial temporary password", required=True),
            ParameterSpec(name="role", type="string", description="Role clearance ('analyst' or 'admin')", required=False, default="analyst"),
        ],
    ),
    "explain_feature": ActionCapability(
        action_id="explain_feature",
        name="Explain System Feature / Concept",
        description="Answer questions and explain cybersecurity features, mathematical models (TreeSHAP, IAT jitter), or physical data diode concepts using local RAG.",
        category="forensics",
        required_role="analyst",
        requires_confirmation=False,
        offline_supported=True,
        parameters=[
            ParameterSpec(name="topic", type="string", description="Feature or concept to explain", required=True)
        ],
    ),
}
