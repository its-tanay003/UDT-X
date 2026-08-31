import React from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Flame,
  Network,
  ShieldAlert,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import type { Alert, Incident } from "../types/soc";

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { incidents, alerts } = useLiveStore();

  const incident: Incident | undefined = incidents.find((i) => i.incident_id === id);

  // If incident not found in store, render empty selection state
  if (!id || !incident) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/monitor")}
              className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] tracking-tight">
              Incident Dossier
            </h1>
          </div>
        </div>

        <div className="p-12 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 text-center space-y-4 font-mono">
          <Flame className="w-10 h-10 text-[#FF8A3D] mx-auto opacity-70" />
          <h3 className="text-base font-bold text-[#E7ECF5]">NO INCIDENT SELECTED</h3>
          <p className="text-xs text-[#8A95AA] max-w-md mx-auto">
            Please select a correlated multi-stage incident from the Live Monitor or Security Overview to inspect its chronological kill-chain progression.
          </p>
          <button
            onClick={() => navigate("/monitor")}
            className="px-4 py-2 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] text-xs font-bold hover:bg-[#3FC7D4]/25 transition-all"
          >
            VIEW LIVE MONITOR ALERTS →
          </button>
        </div>
      </div>
    );
  }

  const memberAlerts = alerts.filter((a) => incident.alert_ids.includes(a.alert_id));

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/monitor")}
            className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
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
          <div id="tour-incident-timeline" className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
              Chronological Kill-Chain Progression (30m Temporal Window)
            </h3>

            {memberAlerts.length > 0 ? (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#3FC7D4]/30">
                {memberAlerts.map((alt, idx) => (
                  <div key={alt.alert_id} className="relative group">
                    <div className="absolute -left-5.5 top-1.5 w-3.5 h-3.5 rounded-full bg-[#0B1220] border-2 border-[#3FC7D4] group-hover:border-[#FF4757] transition-colors" />

                    <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 hover:border-[#3FC7D4]/40 transition-colors">
                      <div className="flex items-center justify-between font-mono text-xs">
                        <span className="text-[#3FC7D4] font-bold">
                          STAGE {idx + 1}: {alt.threat_class}
                        </span>
                        <span className="text-[#8A95AA]">
                          {new Date(alt.timestamp).toLocaleTimeString()}
                        </span>
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
                        <Link
                          to={`/alerts/${alt.alert_id}/evidence`}
                          className="text-[#3FC7D4] hover:underline"
                        >
                          INSPECT EVIDENCE →
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-[#0B1220] rounded-lg text-xs font-mono text-[#8A95AA]">
                Alert metadata hydrating for member IDs: {incident.alert_ids.join(", ")}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Reasoning & Forensic Graph Pivot */}
        <div className="lg:col-span-5 space-y-4">
          <div id="tour-incident-reasoning" className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
            <h3 className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider mb-3">
              Correlation Graph Inference Engine
            </h3>
            <p className="text-xs text-[#8A95AA] leading-relaxed">
              Temporal sliding-window graph correlation connected these alerts into a single
              unified intrusion dossier based on shared pivot entities across a 30-minute graph window.
            </p>

            <div className="mt-4 p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-xs space-y-2">
              <div className="flex justify-between text-[#8A95AA]">
                <span>Incident Window:</span>
                <span className="text-[#E7ECF5]">30 Minutes Rolling</span>
              </div>
              <div className="flex justify-between text-[#8A95AA]">
                <span>Member Alerts:</span>
                <span className="text-[#E7ECF5]">{incident.alert_ids.length} Correlated</span>
              </div>
              <div className="flex justify-between text-[#8A95AA]">
                <span>Graph Edge Type:</span>
                <span className="text-[#3FC7D4]">:PART_OF Incident</span>
              </div>
            </div>

            <Link
              to="/graph"
              className="mt-4 w-full py-2.5 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] hover:bg-[#3FC7D4]/25 font-mono text-xs font-bold transition-all flex items-center justify-center gap-2"
            >
              <Network className="w-4 h-4" />
              VIEW INCIDENT IN NEO4J GRAPH CANVAS
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
