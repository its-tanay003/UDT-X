/**
 * Offline AI Copilot & Local RAG Knowledge Engine.
 * Provides fallback intelligence when air-gapped or disconnected from Core API.
 */

import { CLIENT_ACTION_REGISTRY, CLIENT_ROUTE_REGISTRY } from "./capabilityRegistry";
import type { ActionCapability } from "./capabilityRegistry";

export interface OfflineActionStage {
  id: string;
  action_id: string;
  parameters: Record<string, any>;
  timestamp: string;
  user_email: string;
  status: "staged_offline" | "synced" | "cancelled";
}

export interface OfflineCopilotResponse {
  message: string;
  intent: string;
  confidence: number;
  is_offline: true;
  tool_call?: {
    tool_name: string;
    parameters: Record<string, any>;
    target_route?: string;
  };
  requires_user_confirmation?: boolean;
  confirmation_payload?: any;
  suggested_routes: string[];
  recommendations: Array<{
    id: string;
    title: string;
    reasoning: string;
    target_route: string;
    badge: string;
    priority: string;
  }>;
  staged_action?: OfflineActionStage;
}

const OFFLINE_KNOWLEDGE: Record<string, string> = {
  treeshap:
    "TreeSHAP (Tree SHapley Additive exPlanations) is a mathematical framework for explaining tree-based models (LightGBM). It reveals feature attribution weights for each anomaly score in the Evidence Explorer.",
  diode:
    "A Physical Data Diode is a hardware device that permits unidirectional fiber optical packet flow into the UDT-X enclave. It prevents return-path attacks and ensures zero-transmit passivity.",
  kill_chain:
    "Kill-chain progression in UDT-X correlates multi-stage attacks (Recon -> C2 Beaconing -> Exfiltration) across 30-minute rolling Neo4j graph windows.",
  ddos:
    "The DDoS Surge Detection Engine inspects volumetric packet rates, SYN flag surges, and baseline variance in real-time.",
  c2:
    "The C2 Beaconing Engine calculates Inter-Arrival Time (IAT) periodicity and jitter coefficient to detect automated Command & Control channels.",
  dga:
    "The DGA & DNS Tunneling Engine analyzes domain entropy and high-density TXT record payloads.",
  siem:
    "UDT-X supports ArcSight Common Event Format (CEF) and RFC 5424 Syslog exports with 100% MITRE ATT&CK mapping.",
};

const STAGING_STORAGE_KEY = "udtx_offline_staged_actions";

export class OfflineCopilotEngine {
  static getStagedActions(): OfflineActionStage[] {
    try {
      const raw = localStorage.getItem(STAGING_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  static stageAction(action_id: string, params: Record<string, any>, user_email: string): OfflineActionStage {
    const actions = this.getStagedActions();
    const stage: OfflineActionStage = {
      id: `stage_${Date.now()}`,
      action_id,
      parameters: params,
      timestamp: new Date().toISOString(),
      user_email,
      status: "staged_offline",
    };
    actions.push(stage);
    localStorage.setItem(STAGING_STORAGE_KEY, JSON.stringify(actions));
    return stage;
  }

  static processQuery(
    query: string,
    userRole: "analyst" | "admin",
    userDisplayName: string,
    userEmail: string,
    currentRoute: string = "/"
  ): OfflineCopilotResponse {
    const q = query.trim().toLowerCase();

    // Default offline recommendations
    const recommendations = [
      {
        id: "rec_offline_monitor",
        title: "Inspect Buffered Live Telemetry",
        reasoning: "Review locally buffered packet flows and MITRE tags stored in your browser session.",
        target_route: "/monitor",
        badge: "OFFLINE TELEMETRY",
        priority: "medium",
      },
      {
        id: "rec_offline_replay",
        title: "Test Detection Logic in Replay Lab",
        reasoning: "Offline simulation templates remain fully functional on local client state.",
        target_route: "/replay",
        badge: "SIMULATION",
        priority: "info",
      },
      {
        id: "rec_offline_graph",
        title: "Explore 3D Topology Graph",
        reasoning: "Inspect currently cached enclave node relationships and Bezier communication arcs.",
        target_route: "/graph",
        badge: "TOPOLOGY",
        priority: "info",
      },
    ];

    // 1. Navigation resolution
    if (q.includes("overview") || q.includes("command center") || q.includes("home")) {
      return {
        message: "Offline Copilot: Navigating to Security Command Center (/ overview).",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/" }, target_route: "/" },
        suggested_routes: ["/"],
        recommendations,
      };
    }

    if (q.includes("monitor") || q.includes("live") || q.includes("feed") || q.includes("flows")) {
      return {
        message: "Offline Copilot: Opening Live Telemetry Monitor (/monitor). Displaying cached stream.",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/monitor" }, target_route: "/monitor" },
        suggested_routes: ["/monitor"],
        recommendations,
      };
    }

    if (q.includes("alerts") || q.includes("evidence")) {
      return {
        message: "Offline Copilot: Opening Alerts & Evidence Explorer (/alerts).",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/alerts" }, target_route: "/alerts" },
        suggested_routes: ["/alerts"],
        recommendations,
      };
    }

    if (q.includes("incident") || q.includes("kill chain") || q.includes("dossier")) {
      return {
        message: "Offline Copilot: Opening Security Incidents Dossier Index (/incidents).",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/incidents" }, target_route: "/incidents" },
        suggested_routes: ["/incidents"],
        recommendations,
      };
    }

    if (q.includes("graph") || q.includes("topology") || q.includes("3d")) {
      return {
        message: "Offline Copilot: Loading 3D Network Evidence Graph (/graph).",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/graph" }, target_route: "/graph" },
        suggested_routes: ["/graph"],
        recommendations,
      };
    }

    if (q.includes("threat") || q.includes("sonar") || q.includes("radar")) {
      return {
        message: "Offline Copilot: Opening Threat Intelligence Center (/threats).",
        intent: "navigate",
        confidence: 0.95,
        is_offline: true,
        tool_call: { tool_name: "navigate_page", parameters: { target_route: "/threats" }, target_route: "/threats" },
        suggested_routes: ["/threats"],
        recommendations,
      };
    }

    if (q.includes("replay") || q.includes("simulate") || q.includes("attack")) {
      const scenario = q.includes("ddos") ? "ddos_syn_flood" : q.includes("c2") ? "c2_heartbeat" : "full_kill_chain";
      return {
        message: `Offline Copilot: Replay Lab is ready. Do you want to inject a local synthetic '${scenario}' attack simulation?`,
        intent: "simulate_attack",
        confidence: 0.95,
        is_offline: true,
        requires_user_confirmation: true,
        confirmation_payload: {
          action_id: "trigger_replay_simulation",
          parameters: { scenario },
          prompt: `Confirm offline injection of '${scenario}' simulation into client pipeline?`,
          target_route: "/replay",
        },
        suggested_routes: ["/replay"],
        recommendations,
      };
    }

    if (q.includes("provision") || q.includes("create user")) {
      if (userRole !== "admin") {
        return {
          message: "Offline Copilot: Access Denied. User provisioning requires Administrator clearance.",
          intent: "permission_denied",
          confidence: 1.0,
          is_offline: true,
          suggested_routes: ["/profile"],
          recommendations,
        };
      }
      // Stage in queue since backend is offline
      const staged = this.stageAction("provision_user", { query: q }, userEmail);
      return {
        message: `Offline Mode Active: User provisioning requires connection to the station database. Action has been safely STAGED in your local offline queue (ID: ${staged.id}) and will be processed once connectivity is restored.`,
        intent: "staged_action",
        confidence: 0.90,
        is_offline: true,
        staged_action: staged,
        suggested_routes: ["/profile"],
        recommendations,
      };
    }

    // 2. Knowledge Retrieval (Local RAG)
    for (const [key, text] of Object.entries(OFFLINE_KNOWLEDGE)) {
      if (q.includes(key)) {
        return {
          message: `[Offline Local RAG] ${text}`,
          intent: "explain_concept",
          confidence: 0.92,
          is_offline: true,
          suggested_routes: ["/monitor", "/alerts", "/replay"],
          recommendations,
        };
      }
    }

    // 3. General Fallback
    return {
      message: `[Offline AI Sentinel] Operator ${userDisplayName}, the station is currently operating in Air-Gapped / Offline Fallback Mode. All local navigation, cached telemetry inspection, 3D topology exploration, and Replay Lab simulations remain available. Online-only actions will be staged in your offline queue.`,
      intent: "offline_assistance",
      confidence: 0.85,
      is_offline: true,
      suggested_routes: ["/monitor", "/incidents", "/threats", "/replay"],
      recommendations,
    };
  }
}
