import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Clock,
  ExternalLink,
  Flame,
  Globe,
  Layers,
  Network,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import type { Alert, Incident } from "../types/soc";

interface IncidentDetailProps {
  incidentId?: string;
  onBack?: () => void;
  onSelectAlert?: (alertId: string) => void;
  onNavigateGraph?: () => void;
}

export const IncidentDetailPage: React.FC<IncidentDetailProps> = ({
  incidentId = "INC-20260827-01",
  onBack,
  onSelectAlert,
  onNavigateGraph,
}) => {
  const { incidents, alerts } = useLiveStore();

  const incident: Incident =
    incidents.find((i) => i.incident_id === incidentId) || {
      incident_id: incidentId,
      alert_ids: ["ALT-RECON-001", "ALT-BEACON-002", "ALT-EXFIL-003"],
      window_start: new Date(Date.now() - 3600000).toISOString(),
      window_end: new Date().toISOString(),
      risk_score: 96.5,
      attack_chain: "FULL_KILL_CHAIN",
      host: "192.168.1.105",
      threat_classes: ["RECONNAISSANCE", "C2_BEACONING", "EXFILTRATION"],
    };

  const correlatedAlerts: Alert[] = [
    {
      alert_id: "ALT-RECON-001",
      timestamp: "12:00:15",
      flow_id: "flow-01",
      src_ip: "192.168.1.105",
      dst_ip: "10.0.0.1",
      threat_class: "RECONNAISSANCE",
      severity: "medium",
      confidence: 0.89,
      risk_score: 65.0,
      evidence: [{ label: "SYN Probe Ratio", value: "0.96 (120 ports/s)" }],
      mitre: ["T1046"],
    },
    {
      alert_id: "ALT-BEACON-002",
      timestamp: "12:05:40",
      flow_id: "flow-02",
      src_ip: "192.168.1.105",
      dst_ip: "198.51.100.22",
      threat_class: "C2_BEACONING",
      severity: "high",
      confidence: 0.94,
      risk_score: 88.0,
      evidence: [{ label: "IAT Periodicity", value: "60.02s (Jitter 0.04s)" }],
      mitre: ["T1071.004"],
    },
    {
      alert_id: "ALT-EXFIL-003",
      timestamp: "12:12:08",
      flow_id: "flow-03",
      src_ip: "192.168.1.105",
      dst_ip: "203.0.113.5",
      threat_class: "EXFILTRATION",
      severity: "critical",
      confidence: 0.98,
      risk_score: 94.5,
      evidence: [{ label: "Outbound Volume", value: "8.4 MB (+5.4σ)" }],
      mitre: ["T1048"],
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-[#3FC7D4]">
              <Flame className="w-3.5 h-3.5 text-[#FF4757]" />
              <span className="font-bold uppercase tracking-wider">
                Correlated Attack Chain Incident
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              {incident.incident_id} // {incident.attack_chain || "CORRELATED_APT"}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="px-3 py-1.5 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/30 text-[#FF4757] font-bold">
            RISK: {incident.risk_score.toFixed(1)} / 100
          </div>
        </div>
      </div>

      {/* Grid: Overview Details + "Why These Were Grouped" */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Attack Timeline & Kill Chain Stages */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
              Chronological Kill-Chain Progression (30m Temporal Window)
            </h3>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#3FC7D4]/30">
              {correlatedAlerts.map((alt, idx) => (
                <div key={alt.alert_id} className="relative group">
                  {/* Step Dot */}
                  <div className="absolute -left-[22px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#0B1220] border-2 border-[#3FC7D4] group-hover:border-[#FF4757] transition-colors" />

                  <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 hover:border-[#3FC7D4]/40 transition-colors">
                    <div className="flex items-center justify-between font-mono text-xs">
                      <span className="text-[#3FC7D4] font-bold">STAGE {idx + 1}: {alt.threat_class}</span>
                      <span className="text-[#8A95AA]">{alt.timestamp}</span>
                    </div>

                    <div className="mt-2 font-mono text-xs flex items-center justify-between">
                      <span className="text-[#E7ECF5]">
                        {alt.src_ip} → <span className="text-[#8A95AA]">{alt.dst_ip}</span>
                      </span>
                      <span
                        className="font-bold"
                        style={{
                          color:
                            alt.severity === "critical"
                              ? "#FF4757"
                              : alt.severity === "high"
                              ? "#FF8A3D"
                              : "#3FC7D4",
                        }}
                      >
                        Risk: {alt.risk_score}
                      </span>
                    </div>

                    <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#3FC7D4]/10 text-[11px] font-mono">
                      <span className="text-[#8A95AA]">
                        MITRE: <strong className="text-[#E7ECF5]">{alt.mitre.join(", ")}</strong>
                      </span>
                      <button
                        onClick={() => onSelectAlert && onSelectAlert(alt.alert_id)}
                        className="text-[#3FC7D4] hover:underline"
                      >
                        INSPECT EVIDENCE →
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Reasoning & Forensic Graph Pivot */}
        <div className="lg:col-span-5 space-y-4">
          {/* Why Grouped Reasoning Panel */}
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
            <h3 className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider mb-3">
              Correlation Graph Inference Engine
            </h3>
            <p className="text-xs text-[#8A95AA] leading-relaxed">
              Temporal sliding-window graph correlation connected these 3 alerts into a single
              unified intrusion dossier based on shared pivot host <strong className="text-[#3FC7D4]">192.168.1.105</strong>.
            </p>

            <div className="mt-4 p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-xs space-y-2">
              <div className="flex justify-between text-[#8A95AA]">
                <span>Pivot Entity:</span>
                <span className="text-[#E7ECF5]">Host 192.168.1.105</span>
              </div>
              <div className="flex justify-between text-[#8A95AA]">
                <span>Correlated Stages:</span>
                <span className="text-[#E7ECF5]">Recon → C2 → Exfiltration</span>
              </div>
              <div className="flex justify-between text-[#8A95AA]">
                <span>Graph Relationship:</span>
                <span className="text-[#3FC7D4]">:PART_OF Incident</span>
              </div>
            </div>

            <button
              onClick={onNavigateGraph}
              className="mt-4 w-full py-2.5 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] hover:bg-[#3FC7D4]/25 font-mono text-xs font-bold transition-all flex items-center justify-center gap-2"
            >
              <Network className="w-4 h-4" />
              VIEW INCIDENT IN NEO4J GRAPH CANVAS
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
