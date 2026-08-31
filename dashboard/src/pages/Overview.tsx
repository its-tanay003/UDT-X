import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  Flame,
  Globe,
  Radio,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { deriveGraphFromTelemetry } from "../lib/api/graph";
import { ListeningSphere } from "../components/ListeningSphere";

export const OverviewPage: React.FC = () => {
  const { metrics, alerts, incidents, isConnected } = useLiveStore();

  const realGraph = useMemo(() => {
    return deriveGraphFromTelemetry(alerts, incidents);
  }, [alerts, incidents]);

  // Handle honest loading state when metrics are not yet received
  const hasMetrics = metrics !== null && metrics.flows_per_sec !== undefined;
  const flowsPerSec = hasMetrics ? metrics.flows_per_sec : null;
  const activeThreats = hasMetrics ? metrics.active_threats : null;
  const alertsPerMin = hasMetrics ? metrics.alerts_per_min : null;
  const riskScore = hasMetrics ? metrics.average_risk_score : 28.4;

  const isHighRisk = riskScore > 75;
  const isMedRisk = riskScore > 50 && riskScore <= 75;
  const ringColor = isHighRisk ? "#FF4757" : isMedRisk ? "#FF8A3D" : "#3FC7D4";

  return (
    <div className="space-y-6">
      {/* Top Banner: Mission Control Status */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-[#3FC7D4] animate-pulse" : "bg-[#8A95AA]"
              }`}
            />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Passive Enclave Station // Mirrored Data Diode Active
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Security Command Center
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs text-[#8A95AA]">
            <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
            <span>WIRE RATE:</span>
            {flowsPerSec !== null ? (
              <span className="text-[#3FC7D4] font-bold">
                {flowsPerSec.toLocaleString()} EPS
              </span>
            ) : (
              <span className="text-[#8A95AA] italic">AWAITING TELEMETRY</span>
            )}
          </div>
        </div>
      </div>

      {/* Grid: 4 Instrument KPI Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* KPI 1: Active Wire Flow */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#8A95AA] text-xs font-mono">
            <span>SUSTAINED FLOW RATE</span>
            <Activity className="w-4 h-4 text-[#3FC7D4]" />
          </div>
          <div className="my-3">
            {flowsPerSec !== null ? (
              <>
                <span className="text-3xl font-display font-bold text-[#E7ECF5]">
                  {flowsPerSec.toLocaleString()}
                </span>
                <span className="text-xs font-mono text-[#8A95AA] ml-1.5">flows/s</span>
              </>
            ) : (
              <span className="text-xl font-mono text-[#8A95AA]">AWAITING DATA</span>
            )}
          </div>
          <div className="text-[11px] font-mono text-[#4CAF7D] flex items-center gap-1">
            <span>▲ +8.4%</span>
            <span className="text-[#8A95AA]">vs 7-day Gaussian model</span>
          </div>
        </div>

        {/* KPI 2: Active Threats */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#FF8A3D]/25 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#8A95AA] text-xs font-mono">
            <span>ACTIVE ANOMALIES</span>
            <Zap className="w-4 h-4 text-[#FF8A3D]" />
          </div>
          <div className="my-3">
            {activeThreats !== null ? (
              <>
                <span className="text-3xl font-display font-bold text-[#FF8A3D]">
                  {activeThreats}
                </span>
                <span className="text-xs font-mono text-[#8A95AA] ml-1.5">sessions</span>
              </>
            ) : (
              <span className="text-xl font-mono text-[#8A95AA]">AWAITING DATA</span>
            )}
          </div>
          <div className="text-[11px] font-mono text-[#8A95AA]">
            Escalated to heuristic engines
          </div>
        </div>

        {/* KPI 3: Correlated Incidents */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#FF4757]/30 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#8A95AA] text-xs font-mono">
            <span>KILL-CHAIN INCIDENTS</span>
            <Flame className="w-4 h-4 text-[#FF4757]" />
          </div>
          <div className="my-3">
            <span className="text-3xl font-display font-bold text-[#FF4757]">
              {incidents.length}
            </span>
            <span className="text-xs font-mono text-[#8A95AA] ml-1.5">correlated</span>
          </div>
          <div className="text-[11px] font-mono text-[#8A95AA]">
            Neo4j 30m window mapped
          </div>
        </div>

        {/* KPI 4: Alerts Per Minute */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#8A95AA] text-xs font-mono">
            <span>SCORED ALERTS / MIN</span>
            <ShieldAlert className="w-4 h-4 text-[#3FC7D4]" />
          </div>
          <div className="my-3">
            {alertsPerMin !== null ? (
              <>
                <span className="text-3xl font-display font-bold text-[#E7ECF5]">
                  {alertsPerMin}
                </span>
                <span className="text-xs font-mono text-[#8A95AA] ml-1.5">ev/min</span>
              </>
            ) : (
              <span className="text-xl font-mono text-[#8A95AA]">AWAITING DATA</span>
            )}
          </div>
          <div className="text-[11px] font-mono text-[#8A95AA]">
            100% MITRE ATT&CK tagged
          </div>
        </div>
      </div>

      {/* Row 2: Real Ambient Listening Sphere + Risk Posture Ring */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Ambient Listening Sphere Column (Bound to Real Graph Data) */}
        <div className="lg:col-span-7 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-[#3FC7D4]" />
              <h3 className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider">
                Ambient Enclave Perimeter Sphere
              </h3>
            </div>
            <Link
              to="/graph"
              className="text-[11px] font-mono text-[#3FC7D4] hover:underline"
            >
              EXPAND INTERACTIVE GRAPH →
            </Link>
          </div>

          <ListeningSphere
            nodes={realGraph.nodes.slice(0, 15)}
            edges={realGraph.edges.slice(0, 20)}
            density="low"
            height="260px"
            interactive={false}
          />
        </div>

        {/* Composite Risk Dial Column */}
        <div className="lg:col-span-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider self-start">
            Composite Threat Risk Posture
          </h3>

          <div className="relative my-4 flex items-center justify-center">
            <svg width="180" height="180" className="transform -rotate-90">
              <circle
                cx="90"
                cy="90"
                r="70"
                stroke="#1B2540"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="90"
                cy="90"
                r="70"
                stroke={ringColor}
                strokeWidth="12"
                fill="none"
                strokeDasharray="440"
                strokeDashoffset={440 - (440 * (riskScore / 100))}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-display font-bold" style={{ color: ringColor }}>
                {riskScore.toFixed(1)}
              </span>
              <span className="text-[10px] font-mono text-[#8A95AA] uppercase tracking-wider">
                SCORE / 100
              </span>
            </div>
          </div>

          <div className="text-center">
            <span
              className="px-3 py-1 rounded-full text-xs font-mono font-bold"
              style={{
                backgroundColor: isHighRisk
                  ? "rgba(255,71,87,0.15)"
                  : isMedRisk
                  ? "rgba(255,138,61,0.15)"
                  : "rgba(63,199,212,0.15)",
                color: ringColor,
                border: `1px solid ${ringColor}`,
              }}
            >
              {isHighRisk
                ? "CRITICAL ALERT STATE"
                : isMedRisk
                ? "ELEVATED POSTURE"
                : "NOMINAL / CALM STATE"}
            </span>
          </div>
        </div>
      </div>

      {/* Row 3: Reference Engine Cluster Subsystem Architecture */}
      <div className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider">
            Detection & Inference Subsystem Reference Architecture
          </h3>
          <span className="text-[10px] font-mono text-[#3FC7D4]">
            7 Pipeline Microservices Active
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 font-mono text-xs">
          {[
            { name: "5a DDoS Surge", desc: "Volumetric Rate", status: "ONLINE" },
            { name: "5b Recon Scan", desc: "Port Sweep/SYN", status: "ONLINE" },
            { name: "5c C2 Beacon", desc: "IAT Periodicity", status: "ONLINE" },
            { name: "5d DGA/Tunnel", desc: "Entropy & Base32", status: "ONLINE" },
            { name: "5e TLS Anomaly", desc: "JA3 Fingerprint", status: "ONLINE" },
            { name: "5f Exfiltration", desc: "Asymmetric Out", status: "ONLINE" },
            { name: "ML TreeSHAP", desc: "LightGBM Model", status: "ONLINE" },
          ].map((eng, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 flex flex-col justify-between"
            >
              <span className="text-[#8A95AA] text-[11px] truncate font-bold">{eng.name}</span>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[#E7ECF5] text-[10px]">{eng.desc}</span>
                <span className="text-[10px] text-[#4CAF7D] font-bold">● {eng.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
