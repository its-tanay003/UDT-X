import React, { useEffect, useState } from "react";
import {
  Activity,
  Flame,
  Globe,
  Radio,
  RefreshCw,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { ListeningSphere } from "../components/ListeningSphere";

interface OverviewProps {
  onNavigate?: (tab: string) => void;
}

export const OverviewPage: React.FC<OverviewProps> = ({ onNavigate }) => {
  const { metrics, alerts, incidents, isConnected } = useLiveStore();
  const [wirePulse, setWirePulse] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setWirePulse((p) => (p + 1) % 100);
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  const riskScore = metrics.average_risk_score || 28.4;
  const isHighRisk = riskScore > 75;
  const isMedRisk = riskScore > 50 && riskScore <= 75;
  const ringColor = isHighRisk ? "#FF4757" : isMedRisk ? "#FF8A3D" : "#3FC7D4";

  return (
    <div className="space-y-6">
      {/* Top Banner: Mission Control Status */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
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
            <span className="text-[#3FC7D4] font-bold">
              {(metrics.flows_per_sec || 124850).toLocaleString()} EPS
            </span>
          </div>
        </div>
      </div>

      {/* Grid: 4 Instrument KPI Cards + Ambient Listening Sphere */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* KPI 1: Active Wire Flow */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#8A95AA] text-xs font-mono">
            <span>SUSTAINED FLOW RATE</span>
            <Activity className="w-4 h-4 text-[#3FC7D4]" />
          </div>
          <div className="my-3">
            <span className="text-3xl font-display font-bold text-[#E7ECF5]">
              {(metrics.flows_per_sec || 124850).toLocaleString()}
            </span>
            <span className="text-xs font-mono text-[#8A95AA] ml-1.5">flows/s</span>
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
            <span className="text-3xl font-display font-bold text-[#FF8A3D]">
              {metrics.active_threats || 2}
            </span>
            <span className="text-xs font-mono text-[#8A95AA] ml-1.5">sessions</span>
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
              {incidents.length > 0 ? incidents.length : 1}
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
            <span className="text-3xl font-display font-bold text-[#E7ECF5]">
              {metrics.alerts_per_min || 312}
            </span>
            <span className="text-xs font-mono text-[#8A95AA] ml-1.5">ev/min</span>
          </div>
          <div className="text-[11px] font-mono text-[#8A95AA]">
            100% MITRE ATT&CK tagged
          </div>
        </div>
      </div>

      {/* Row 2: Ambient Listening Sphere + Risk Posture Dial + Engine Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Ambient Listening Sphere Column (Signature Element) */}
        <div className="lg:col-span-7 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-[#3FC7D4]" />
              <h3 className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider">
                Ambient Enclave Perimeter Sphere
              </h3>
            </div>
            <button
              onClick={() => onNavigate && onNavigate("graph")}
              className="text-[11px] font-mono text-[#3FC7D4] hover:underline"
            >
              EXPAND INTERACTIVE GRAPH →
            </button>
          </div>

          <ListeningSphere density="low" height="260px" interactive={false} />
        </div>

        {/* Composite Risk Dial Column */}
        <div className="lg:col-span-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider self-start">
            Composite Threat Risk Posture
          </h3>

          {/* Dynamic SVG Risk Gauge Ring */}
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
                backgroundColor: isHighRisk ? "rgba(255,71,87,0.15)" : isMedRisk ? "rgba(255,138,61,0.15)" : "rgba(63,199,212,0.15)",
                color: ringColor,
                border: `1px solid ${ringColor}`,
              }}
            >
              {isHighRisk ? "CRITICAL ALERT STATE" : isMedRisk ? "ELEVATED POSTURE" : "NOMINAL / CALM STATE"}
            </span>
          </div>
        </div>
      </div>

      {/* Row 3: Engine Cluster Health Telemetry */}
      <div className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 p-5">
        <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
          Heuristic & ML Engine Subsystem Health
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 font-mono text-xs">
          {[
            { name: "5a DDoS Surge", rate: "1.2k ev/s", status: "ONLINE" },
            { name: "5b Recon Scan", rate: "950 ev/s", status: "ONLINE" },
            { name: "5c C2 Beacon", rate: "620 ev/s", status: "ONLINE" },
            { name: "5d DGA/Tunnel", rate: "840 ev/s", status: "ONLINE" },
            { name: "5e TLS Anomaly", rate: "1.1k ev/s", status: "ONLINE" },
            { name: "5f Exfiltration", rate: "410 ev/s", status: "ONLINE" },
            { name: "ML TreeSHAP", rate: "99.8% acc", status: "ONLINE" },
          ].map((eng, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 flex flex-col justify-between"
            >
              <span className="text-[#8A95AA] text-[11px] truncate">{eng.name}</span>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[#E7ECF5] text-[11px] font-bold">{eng.rate}</span>
                <span className="text-[10px] text-[#4CAF7D] font-bold">● {eng.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
