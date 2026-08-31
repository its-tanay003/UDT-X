export type ThreatClass =
  | "DDOS"
  | "RECONNAISSANCE"
  | "C2_BEACONING"
  | "DGA"
  | "DNS_TUNNELING"
  | "ENCRYPTED_ANOMALY"
  | "EXFILTRATION";

export type Severity = "low" | "medium" | "high" | "critical";

export interface FlowEvent {
  flow_id: string;
  timestamp: string;
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
  direction: string;
  bytes: number;
  packets: number;
  duration_ms: number;
  dns?: { query?: string; query_type?: string; rcode?: string };
  tls?: { ja3?: string; sni?: string; cipher_suite?: string };
  source: string;
  schema_version: string;
}

export interface Alert {
  alert_id: string;
  timestamp: string;
  flow_id: string;
  src_ip: string;
  dst_ip: string;
  threat_class: ThreatClass;
  severity: Severity;
  confidence: number;
  risk_score: number;
  evidence: Array<{ label: string; value: number | string }>;
  mitre: string[];
  shap_values?: Array<{ feature: string; contribution: number }>;
}

export interface Incident {
  incident_id: string;
  alert_ids: string[];
  window_start: string;
  window_end: string;
  risk_score: number;
  attack_chain?: string; // e.g. "FULL_KILL_CHAIN"
  host?: string;
  threat_classes?: ThreatClass[];
}

export interface PerformanceMetrics {
  total_alerts: number;
  total_incidents: number;
  critical_alerts: number;
  active_incidents: number;
  average_risk_score: number;
  flows_per_sec: number;
  alerts_per_min: number;
  active_threats: number;
  cpu_usage_pct?: number;
  memory_usage_mb?: number;
  p99_latency_ms?: number;
  median_latency_ms?: number;
  timestamp: string;
}

export type WSMessage =
  | { type: "CONNECTED"; msg: string }
  | { type: "NEW_ALERT"; data: Alert }
  | { type: "NEW_INCIDENT"; data: Incident }
  | { type: "METRICS_UPDATE"; data: Partial<PerformanceMetrics> };
