import React, { useState } from "react";
import {
  Activity,
  ArrowLeft,
  Flame,
  Globe,
  Lock,
  Play,
  Radio,
  RefreshCw,
  Shield,
  ShieldAlert,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { triggerReplayScenario } from "../lib/api/threats";

interface ReplayLabProps {
  onBack?: () => void;
  onSelectAlert?: (alertId: string) => void;
}

interface Scenario {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: any;
  threats: string[];
  mitre: string[];
}

const SCENARIOS: Scenario[] = [
  {
    id: "kill_chain",
    name: "Full APT Kill-Chain Intrusion",
    category: "Multi-Stage Attack Sequence",
    description:
      "Emulates full 3-stage intrusion: Horizontal TCP SYN Port Scanning → C2 Beaconing Channel → Asymmetric Exfiltration Spike.",
    icon: Flame,
    threats: ["RECONNAISSANCE", "C2_BEACONING", "EXFILTRATION"],
    mitre: ["T1046", "T1071.004", "T1048"],
  },
  {
    id: "ddos_surge",
    name: "Volumetric DDoS Surge Flood",
    category: "High-Rate SYN Attack",
    description:
      "Simulates volumetric traffic surge (> 15,000 pkts/s) with 0.99 SYN/ACK asymmetry targeting internal gateway.",
    icon: Zap,
    threats: ["DDOS"],
    mitre: ["T1498.001"],
  },
  {
    id: "dga_c2",
    name: "Algorithmic DGA & DNS Tunnel",
    category: "Domain Fluxing & Exfil",
    description:
      "Generates pseudorandom high-entropy domain queries (4.65 bits/char) and base32 data exfiltration tunneling.",
    icon: Globe,
    threats: ["DGA", "DNS_TUNNELING"],
    mitre: ["T1568.002", "T1071.004"],
  },
  {
    id: "exfiltration_burst",
    name: "Data Exfiltration Volume Spike",
    category: "Asymmetric Outbound Leak",
    description:
      "Transfers 8.4 MB outbound payload (+5.4σ above 7-day Gaussian baseline) over anomalous TCP session.",
    icon: ShieldAlert,
    threats: ["EXFILTRATION"],
    mitre: ["T1048"],
  },
  {
    id: "encrypted_anomaly",
    name: "TLS Encrypted Session Anomaly",
    category: "JA3 Fingerprint Anomaly",
    description:
      "Simulates encrypted TLS tunnel with self-signed certificate, SNI mismatch, and high byte distribution entropy.",
    icon: Lock,
    threats: ["ENCRYPTED_ANOMALY"],
    mitre: ["T1573.002"],
  },
];

export const ReplayLabPage: React.FC<ReplayLabProps> = ({
  onBack,
  onSelectAlert,
}) => {
  const { alerts, incidents, isConnected } = useLiveStore();
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);
  const [statusLog, setStatusLog] = useState<string[]>([]);
  const [armedMap, setArmedMap] = useState<Record<string, boolean>>({
    kill_chain: true,
  });

  const toggleArm = (id: string) => {
    setArmedMap((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleArmAndExecute = async (scenario: Scenario) => {
    setActiveScenarioId(scenario.id);
    const ts = new Date().toLocaleTimeString();
    setStatusLog((prev) => [
      `[${ts}] DISPATCHING ${scenario.name} to Replay Engine...`,
      ...prev.slice(0, 10),
    ]);

    try {
      const res = await triggerReplayScenario(scenario.id, "http://localhost:8000");
      const doneTs = new Date().toLocaleTimeString();
      setStatusLog((prev) => [
        `[${doneTs}] SCENARIO REPLAYED // ${res.alerts_generated} alerts emitted // incident: ${res.incident_generated}`,
        ...prev.slice(0, 10),
      ]);
    } catch (err) {
      setStatusLog((prev) => [
        `[${ts}] ERROR: Scenario dispatch failed: ${err}`,
        ...prev.slice(0, 10),
      ]);
    } finally {
      setTimeout(() => setActiveScenarioId(null), 1000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
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
              <Sparkles className="w-3.5 h-3.5 text-[#3FC7D4]" />
              <span className="font-bold uppercase tracking-wider">
                SIH Live Evaluation & Demonstration Control Surface
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              Replay Lab // Mission Control Instrument Console
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="px-3 py-1 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#3FC7D4] font-bold">
            SAFE INTERFACE GUARD: ACTIVE
          </span>
        </div>
      </div>

      {/* Grid: 5 Physical Hardware-Style Switch Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: 5 Simulation Control Cards */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider">
              Attack Simulation Presets (Toggle Switch + Engage)
            </h3>
            <span className="text-[11px] font-mono text-[#3FC7D4]">5 Presets Armed</span>
          </div>

          <div className="space-y-3.5">
            {SCENARIOS.map((sc) => {
              const Icon = sc.icon;
              const isArmed = armedMap[sc.id] ?? false;
              const isRunning = activeScenarioId === sc.id;

              return (
                <div
                  key={sc.id}
                  className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 hover:border-[#3FC7D4]/35 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#3FC7D4]">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-base font-display font-bold text-[#E7ECF5]">
                          {sc.name}
                        </h4>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0B1220] text-[#3FC7D4] border border-[#3FC7D4]/20">
                          {sc.category}
                        </span>
                      </div>
                      <p className="text-xs text-[#8A95AA] mt-1 max-w-xl leading-relaxed">
                        {sc.description}
                      </p>
                      <div className="mt-2.5 flex items-center gap-3 text-[10px] font-mono text-[#8A95AA]">
                        <span>THREATS: <strong className="text-[#E7ECF5]">{sc.threats.join(", ")}</strong></span>
                        <span>MITRE: <strong className="text-[#3FC7D4]">{sc.mitre.join(", ")}</strong></span>
                      </div>
                    </div>
                  </div>

                  {/* Hardware Switch Controls */}
                  <div className="flex items-center gap-4 self-end md:self-center">
                    {/* Toggle Switch */}
                    <button
                      onClick={() => toggleArm(sc.id)}
                      className="flex items-center gap-1.5 text-xs font-mono text-[#8A95AA] hover:text-[#E7ECF5]"
                    >
                      {isArmed ? (
                        <ToggleRight className="w-7 h-7 text-[#3FC7D4]" />
                      ) : (
                        <ToggleLeft className="w-7 h-7 text-[#8A95AA]" />
                      )}
                      <span className="text-[10px]">{isArmed ? "ARMED" : "SAFE"}</span>
                    </button>

                    {/* Engage Trigger Button */}
                    <button
                      disabled={!isArmed || isRunning}
                      onClick={() => handleArmAndExecute(sc)}
                      className={`px-4 py-2 rounded-lg font-mono text-xs font-bold transition-all flex items-center gap-2 ${
                        isRunning
                          ? "bg-[#FF4757] text-white animate-pulse"
                          : isArmed
                          ? "bg-[#3FC7D4] text-[#0B1220] hover:bg-[#3FC7D4]/90 shadow-[0_0_15px_rgba(63,199,212,0.25)]"
                          : "bg-[#1B2540] text-[#8A95AA] cursor-not-allowed"
                      }`}
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      {isRunning ? "TRANSMITTING..." : "ENGAGE"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Live Wire Console Stream */}
        <div className="lg:col-span-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-3">
              Station Wire Log (Real-Time)
            </h3>
            <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-xs text-[#3FC7D4] space-y-2 min-h-[300px] overflow-y-auto">
              <div className="text-[#8A95AA] text-[10px] pb-2 border-b border-[#3FC7D4]/10">
                [SYSTEM READY] Listening for simulation dispatch triggers...
              </div>
              {statusLog.map((log, idx) => (
                <div key={idx} className="text-[11px] leading-relaxed">
                  {log}
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-[11px] text-[#8A95AA]">
            <span>EMITTED TELEMETRY:</span>
            <div className="mt-1 flex items-center justify-between text-[#E7ECF5] font-bold">
              <span>{alerts.length} ALERTS ACTIVE</span>
              <span className="text-[#3FC7D4]">{incidents.length} INCIDENTS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
