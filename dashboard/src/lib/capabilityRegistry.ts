/**
 * Client-Side Website Capability Graph & Action Registry.
 * Used by the frontend Copilot and offline fallback resolver.
 */

export interface ParameterSpec {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
  enum_values?: string[];
}

export interface ActionCapability {
  action_id: string;
  name: string;
  description: string;
  category: "navigation" | "telemetry" | "forensics" | "simulation" | "settings" | "admin";
  required_role: "analyst" | "admin";
  requires_confirmation: boolean;
  confirmation_prompt?: string;
  offline_supported: boolean;
  online_fallback_behavior: "execute" | "stage_queue" | "explain_unavailable";
  target_route?: string;
  parameters: ParameterSpec[];
}

export interface RouteCapability {
  route: string;
  name: string;
  description: string;
  min_role: "analyst" | "admin";
  offline_supported: boolean;
  key_features: string[];
  sample_queries: string[];
}

export const CLIENT_ROUTE_REGISTRY: Record<string, RouteCapability> = {
  "/": {
    route: "/",
    name: "Security Command Center / Overview",
    description: "Global enclave operational posture, ambient 3D Listening Sphere, composite threat risk ring, and hardware data diode status.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "3D Ambient Listening Sphere (WebGL passive diode)",
      "Composite Risk Dial (0-100 hazard score)",
      "4 Core Instrument KPI cards with live velocity count",
      "Detection & Inference Subsystem Reference Architecture",
    ],
    sample_queries: [
      "Take me to the overview",
      "What is our composite risk score?",
      "Show me the command center",
    ],
  },
  "/monitor": {
    route: "/monitor",
    name: "Live Telemetry Monitor",
    description: "Continuous zero-latency streaming table of inbound network flows and detected anomalies across the passive mirror tap.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Zero-refresh streaming table via WebSocket",
      "Severity & threat category filters",
      "Sub-second IP and hash search",
      "Quick-pivot links to explainable AI evidence",
    ],
    sample_queries: [
      "Show me the live monitor",
      "Filter for critical alerts in the live stream",
      "Are there any active DDoS anomalies streaming right now?",
    ],
  },
  "/alerts": {
    route: "/alerts",
    name: "Alerts & Evidence Explorer Index",
    description: "Comprehensive index of scored security alerts with MITRE ATT&CK technique tags and 1-click SIEM export.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "ArcSight CEF and RFC 5424 Syslog batch exporters",
      "Class and severity multi-parameter filters",
      "Staggered entrance table and mobile card view",
    ],
    sample_queries: [
      "Open the alerts list",
      "Export alerts to CEF",
      "Show all C2 beaconing alerts",
    ],
  },
  "/incidents": {
    route: "/incidents",
    name: "Security Incidents Dossier Index",
    description: "Chronological multi-stage attack chains synthesized across 30-minute rolling Neo4j graph windows.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Sortable incident cards by risk score, timestamp, and alert volume",
      "Correlated threat class tags",
      "Affected host and temporal window metadata",
    ],
    sample_queries: [
      "Show me all incidents",
      "What are the highest risk attack chains?",
      "List active APT incidents",
    ],
  },
  "/graph": {
    route: "/graph",
    name: "3D Network Evidence Graph",
    description: "Full-screen interactive 3D WebGL topological graph mapping communicating hosts and inbound data diode flows.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Interactive orbital camera with bloom post-processing",
      "Click-to-inspect host nodes",
      "Directional Bezier communication arcs",
    ],
    sample_queries: [
      "Open the 3D network graph",
      "Inspect the host topology",
      "Show communicating nodes",
    ],
  },
  "/threats": {
    route: "/threats",
    name: "Threat Intelligence Center",
    description: "Polar coordinate radar sweep visualization mapping threat distributions, MITRE matrices, and severity wedges.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "D3 polar sonar radar sweep",
      "Threat class distribution wedges",
      "Historical temporal filters (1h, 24h, 7d, 30d)",
    ],
    sample_queries: [
      "Show threat intelligence sonar",
      "What MITRE techniques are most active?",
      "Open the threat center",
    ],
  },
  "/replay": {
    route: "/replay",
    name: "Deterministic Replay Lab",
    description: "Hardware-isolated simulation console with physical-style toggle switches to inject synthetic attack scenarios safely.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Pre-configured attack templates (APT Kill-Chain, DDoS, DGA C2, Exfil)",
      "Safety interlock guard",
      "Synthetic packet stream injector",
    ],
    sample_queries: [
      "Go to Replay Lab",
      "Simulate a multi-stage APT attack",
      "Test detection engines with synthetic traffic",
    ],
  },
  "/performance": {
    route: "/performance",
    name: "Performance & SLA Telemetry",
    description: "System throughput benchmarks sustaining 124,850+ EPS with sub-5ms latency and zero packet loss.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Events Per Second wire rate meters",
      "P50, P95, P99 inference latency tracking",
      "Microservice memory and CPU utilization",
    ],
    sample_queries: [
      "What is our current wire rate?",
      "Show performance and latency metrics",
      "Check system SLA",
    ],
  },
  "/profile": {
    route: "/profile",
    name: "Operator Profile & Identity",
    description: "Analyst credential management, station password changes, and administrator user provisioning.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Callsign & display name updates",
      "Password changes with bcrypt verification",
      "Administrator user provisioning table",
    ],
    sample_queries: [
      "Open my profile",
      "Change my password",
      "Provision a new analyst account",
    ],
  },
  "/settings": {
    route: "/settings",
    name: "Station Settings & Diagnostics",
    description: "Audio alert toggles, 3D particle density tuning, default SIEM format, and station tour triggers.",
    min_role: "analyst",
    offline_supported: true,
    key_features: [
      "Critical threat audio pings",
      "3D Listening Sphere GPU particle density selector",
      "Replay Station Tour & Reset Briefing actions",
    ],
    sample_queries: [
      "Open station settings",
      "Disable critical sound alerts",
      "Replay the onboarding tour",
    ],
  },
};

export const CLIENT_ACTION_REGISTRY: Record<string, ActionCapability> = {
  navigate_page: {
    action_id: "navigate_page",
    name: "Navigate Website Page",
    description: "Safely navigate the operator to any available console screen or dossier route.",
    category: "navigation",
    required_role: "analyst",
    requires_confirmation: false,
    offline_supported: true,
    online_fallback_behavior: "execute",
    parameters: [
      {
        name: "target_route",
        type: "string",
        description: "The destination path",
        required: true,
      },
    ],
  },
  filter_alerts: {
    action_id: "filter_alerts",
    name: "Filter & Inspect Alerts",
    description: "Filter buffered alerts by severity level or threat class and navigate to Alerts view.",
    category: "forensics",
    required_role: "analyst",
    requires_confirmation: false,
    offline_supported: true,
    online_fallback_behavior: "execute",
    target_route: "/alerts",
    parameters: [
      {
        name: "severity",
        type: "string",
        description: "Alert severity level",
        required: false,
        enum_values: ["critical", "high", "medium", "low", "ALL"],
      },
      {
        name: "threat_class",
        type: "string",
        description: "Specific threat category",
        required: false,
        enum_values: ["DDOS", "C2_BEACONING", "RECONNAISSANCE", "DGA", "DNS_TUNNELING", "EXFILTRATION", "ALL"],
      },
    ],
  },
  trigger_replay_simulation: {
    action_id: "trigger_replay_simulation",
    name: "Trigger Attack Simulation",
    description: "Inject a synthetic attack scenario into the detection pipeline within the isolated Replay Lab.",
    category: "simulation",
    required_role: "analyst",
    requires_confirmation: true,
    confirmation_prompt: "Are you sure you want to inject a synthetic {scenario} scenario into the local detection pipeline?",
    offline_supported: true,
    online_fallback_behavior: "execute",
    target_route: "/replay",
    parameters: [
      {
        name: "scenario",
        type: "string",
        description: "Attack simulation scenario type",
        required: true,
        default: "full_kill_chain",
        enum_values: ["full_kill_chain", "ddos_syn_flood", "c2_heartbeat", "dns_tunnel_exfil"],
      },
    ],
  },
  export_siem_telemetry: {
    action_id: "export_siem_telemetry",
    name: "Export SIEM Records",
    description: "Trigger an immediate telemetry export formatted in ArcSight CEF or Syslog RFC 5424.",
    category: "telemetry",
    required_role: "analyst",
    requires_confirmation: false,
    offline_supported: true,
    online_fallback_behavior: "execute",
    target_route: "/alerts",
    parameters: [
      {
        name: "format",
        type: "string",
        description: "Export format",
        required: true,
        default: "cef",
        enum_values: ["cef", "syslog", "stix"],
      },
    ],
  },
  provision_user: {
    action_id: "provision_user",
    name: "Provision New Analyst Account",
    description: "Create a new operator identity in the air-gapped station database (Administrator only).",
    category: "admin",
    required_role: "admin",
    requires_confirmation: true,
    confirmation_prompt: "Confirm provisioning new station user '{email}' with role '{role}'?",
    offline_supported: false,
    online_fallback_behavior: "stage_queue",
    target_route: "/profile",
    parameters: [
      { name: "email", type: "string", description: "User enclave email address", required: true },
      { name: "display_name", type: "string", description: "Display call-sign", required: true },
      { name: "password", type: "string", description: "Initial temporary password", required: true },
      { name: "role", type: "string", description: "Role clearance ('analyst' or 'admin')", required: false, default: "analyst" },
    ],
  },
};
