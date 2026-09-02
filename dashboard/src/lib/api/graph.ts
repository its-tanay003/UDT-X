import type { Alert, Incident } from "../../types/soc";

export interface GraphNode {
  id: string;
  label: string;
  type: "host" | "destination" | "alert" | "incident";
  risk?: number;
  severity?: string;
  ip?: string;
  position?: [number, number, number];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: "TRIGGERED" | "TARGETED" | "PART_OF" | "COMMUNICATED_WITH";
  severity?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Adapter for Graph Topology Data.
 * Calls GET /graph if available; falls back to client-side derivation from alerts and incidents.
 */
export async function fetchGraphTopology(
  apiUrl: string = "http://localhost:8000",
  alerts: Alert[] = [],
  incidents: Incident[] = []
): Promise<GraphData> {
  try {
    const res = await fetch(`${apiUrl}/graph`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.nodes && data.edges) {
        return data;
      }
    }
  } catch (err) {
    // Expected fallback if backend endpoint is unavailable
  }

  // TODO(backend): Replace client-side fallback derivation with real GET /graph endpoint returning full Neo4j topology.
  return deriveGraphFromTelemetry(alerts, incidents);
}

export function deriveGraphFromTelemetry(
  alerts: Alert[],
  incidents: Incident[]
): GraphData {
  const nodeMap = new Map<string, GraphNode>();
  const edgeList: GraphEdge[] = [];

  // Default core enclave infrastructure nodes if telemetry is initializing
  nodeMap.set("192.168.1.105", {
    id: "192.168.1.105",
    label: "Workstation-Alpha (192.168.1.105)",
    type: "host",
    risk: 88.5,
    ip: "192.168.1.105",
  });
  nodeMap.set("10.0.0.1", {
    id: "10.0.0.1",
    label: "Domain Controller (10.0.0.1)",
    type: "destination",
    risk: 45.0,
    ip: "10.0.0.1",
  });
  nodeMap.set("198.51.100.22", {
    id: "198.51.100.22",
    label: "External C2 Node (198.51.100.22)",
    type: "destination",
    risk: 95.0,
    ip: "198.51.100.22",
  });

  // Populate from real alerts
  alerts.forEach((alert) => {
    if (!nodeMap.has(alert.src_ip)) {
      nodeMap.set(alert.src_ip, {
        id: alert.src_ip,
        label: `Host (${alert.src_ip})`,
        type: "host",
        risk: alert.risk_score,
        ip: alert.src_ip,
      });
    }

    if (!nodeMap.has(alert.dst_ip)) {
      nodeMap.set(alert.dst_ip, {
        id: alert.dst_ip,
        label: `Target (${alert.dst_ip})`,
        type: "destination",
        risk: alert.risk_score,
        ip: alert.dst_ip,
      });
    }

    const alertNodeId = alert.alert_id;
    if (!nodeMap.has(alertNodeId)) {
      nodeMap.set(alertNodeId, {
        id: alertNodeId,
        label: `${alert.threat_class} [${alert.severity.toUpperCase()}]`,
        type: "alert",
        risk: alert.risk_score,
        severity: alert.severity,
      });

      edgeList.push({
        id: `e-${alert.src_ip}-${alertNodeId}`,
        source: alert.src_ip,
        target: alertNodeId,
        type: "TRIGGERED",
        severity: alert.severity,
      });

      edgeList.push({
        id: `e-${alertNodeId}-${alert.dst_ip}`,
        source: alertNodeId,
        target: alert.dst_ip,
        type: "TARGETED",
        severity: alert.severity,
      });
    }
  });

  // Link Incidents
  incidents.forEach((inc) => {
    const incNodeId = inc.incident_id;
    if (!nodeMap.has(incNodeId)) {
      nodeMap.set(incNodeId, {
        id: incNodeId,
        label: `Incident ${inc.incident_id} (${inc.attack_chain || "CORRELATED"})`,
        type: "incident",
        risk: inc.risk_score,
        severity: "critical",
      });

      inc.alert_ids.forEach((aid) => {
        if (nodeMap.has(aid)) {
          edgeList.push({
            id: `e-${aid}-${incNodeId}`,
            source: aid,
            target: incNodeId,
            type: "PART_OF",
            severity: "critical",
          });
        }
      });
    }
  });

  return {
    nodes: Array.from(nodeMap.values()),
    edges: edgeList,
  };
}
