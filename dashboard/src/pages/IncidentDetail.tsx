import React from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Flame,
  Globe,
  Network,
  ShieldAlert,
  Calendar,
  Layers,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { EmptyState } from "../components/EmptyState";
import { Tooltip } from "../components/Tooltip";
import { getMitreLabel, type Alert, type Incident } from "../types/soc";

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
              onClick={() => navigate("/incidents")}
              className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-2xl font-display font-bold text-[#E7ECF5] tracking-tight">
                Incident Dossier
              </h1>
              <p className="text-xs text-[#8A95AA] mt-0.5">
                In-depth chronological kill-chain progression, affected asset topology, and containment telemetry.
              </p>
            </div>
          </div>
        </div>

        <EmptyState
          icon={Flame}
          title="NO INCIDENT SELECTED"
          description="Please select a correlated multi-stage incident from the Security Incidents Dossier or Security Command Center to inspect its chronological kill-chain progression."
          actionLabel="BROWSE ALL INCIDENTS →"
          actionTo="/app/incidents"
          secondaryActionLabel="VIEW LIVE MONITOR"
          secondaryActionTo="/app/monitor"
          variant="warn"
        />
      </div>
    );
  }

  const memberAlerts = alerts.filter((a) => incident.alert_ids.includes(a.alert_id));

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/incidents")}
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
            <p className="text-xs text-[#8A95AA] mt-0.5">
              In-depth chronological kill-chain progression, affected asset topology, and containment telemetry.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <Tooltip
            title="Composite Incident Risk"
            code="RISK SCORE"
            content="Aggregated hazard level calculated across all correlated multi-stage attack steps."
          >
            <div className="px-3 py-1.5 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/30 text-[#FF4757] font-bold cursor-help">
              RISK: {incident.risk_score.toFixed(1)} / 100
            </div>
          </Tooltip>
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
                    <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 hover:border-[#3FC7D4]/50 transition-colors space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[#3FC7D4]">
                            STAGE {idx + 1}:
                          </span>
                          <span className="font-mono text-xs font-bold text-[#E7ECF5]">
                            {alt.threat_class}
                          </span>
                        </div>
                        <span className="font-mono text-[10px] text-[#8A95AA]">
                          {new Date(alt.timestamp).toLocaleTimeString()}
                        </span>
                      </div>

                      <div className="font-mono text-xs text-[#8A95AA] flex items-center justify-between">
                        <span>
                          {alt.src_ip} → {alt.dst_ip}
                        </span>
                        <span className="text-[#FF4757] font-bold">
                          RISK {alt.risk_score.toFixed(1)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between pt-1 border-t border-[#3FC7D4]/10">
                        <div className="flex gap-1">
                          {alt.mitre?.map((m, mIdx) => {
                            const label = getMitreLabel(m);
                            return (
                              <Tooltip key={`${alt.alert_id}-m-${mIdx}`} content={`MITRE ATT&CK: ${label}`} code={label}>
                                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#131B2E] text-[#8A95AA]">
                                  {label}
                                </span>
                              </Tooltip>
                            );
                          })}
                        </div>
                        <Link
                          to={`/alerts/${alt.alert_id}/evidence`}
                          className="text-[11px] font-mono text-[#3FC7D4] hover:underline"
                        >
                          EVIDENCE BREAKDOWN →
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                compact
                icon={Flame}
                title="NO MEMBER ALERTS BUFFERED"
                description="The individual alerts for this incident were logged before the current session buffer or have been archived."
                actionLabel="VIEW LIVE ALERTS"
                actionTo="/app/alerts"
              />
            )}
          </div>
        </div>

        {/* Right Column: Correlated Asset & Root Cause */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-[#3FC7D4]" />
              <span>CORRELATION HEURISTICS</span>
            </h3>

            <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 space-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Affected Endpoint:</span>
                <span className="text-[#3FC7D4] font-bold">{incident.host || "10.0.0.1 (Gateway)"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Correlated Alerts:</span>
                <span className="text-[#E7ECF5]">{incident.alert_ids.length} alerts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Temporal Window:</span>
                <span className="text-[#E7ECF5]">
                  {new Date(incident.window_start).toLocaleTimeString()} – {new Date(incident.window_end).toLocaleTimeString()}
                </span>
              </div>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <div className="text-[#8A95AA] uppercase text-[10px] tracking-wider">
                Why These Were Correlated:
              </div>
              <p className="text-xs text-[#E7ECF5] leading-relaxed p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                The correlation engine identified a <strong>multi-phase progression</strong> originating from or targeting host{" "}
                <code className="text-[#3FC7D4]">{incident.host || "10.0.0.1"}</code> within a single 30-minute sliding window. The sequence matches known MITRE ATT&CK patterns for reconnaissance leading to persistent command channel deployment.
              </p>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <Link
                to="/app/graph"
                className="w-full text-center py-2 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] font-mono text-xs font-bold hover:bg-[#3FC7D4]/25 transition-all flex items-center justify-center gap-1.5"
              >
                <Network className="w-3.5 h-3.5" />
                <span>INSPECT IN 3D NETWORK GRAPH →</span>
              </Link>
              <Link
                to="/app/incidents"
                className="w-full text-center py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] font-mono text-xs transition-colors"
              >
                ← BACK TO INCIDENTS DOSSIER
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
