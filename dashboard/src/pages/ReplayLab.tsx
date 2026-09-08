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
import { Tooltip } from "../components/Tooltip";

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
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
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
              Deterministic Replay Lab
            </h1>
            <p className="text-xs text-[#8A95AA] mt-0.5">
              Deterministic attack scenario generator for testing detection engines in an isolated sandbox.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <Tooltip
            title="Safe Interface Guard"
            content="Hardware data diode policy prevents attack packets from ever routing into live production interfaces."
          >
            <span className="px-3 py-1 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#3FC7D4] font-bold cursor-help">
              SAFE INTERFACE GUARD: ACTIVE
            </span>
          </Tooltip>
        </div>
      </div>

      {/* Grid: 5 Hardware-Style Switch Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: 5 Simulation Control Cards */}
        <div id="tour-replay-console" className="lg:col-span-8 space-y-4">
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
                  className={`p-5 rounded-xl border transition-all ${
                    isRunning
                      ? "bg-[#1B2540] border-[#FF4757] shadow-[0_0_20px_rgba(255,71,87,0.2)]"
                      : isArmed
                      ? "bg-[#131B2E] border-[#3FC7D4]/30"
                      : "bg-[#0B1220]/70 border-[#3FC7D4]/10 opacity-75"
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-3.5">
                      <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#3FC7D4] mt-0.5">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-display font-bold text-sm text-[#E7ECF5]">
                            {sc.name}
                          </h4>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA]">
                            {sc.category}
                          </span>
                        </div>
                        <p className="text-xs text-[#8A95AA] max-w-xl">
                          {sc.description}
                        </p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {sc.mitre.map((m) => (
                            <Tooltip key={m} content={`MITRE ATT&CK: ${m}`} code={m}>
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#0B1220] border border-[#3FC7D4]/15 text-[#3FC7D4]">
                                {m}
                              </span>
                            </Tooltip>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Arm Switch & Execute Button */}
                    <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                      <button
                        type="button"
                        onClick={() => toggleArm(sc.id)}
                        className="flex items-center gap-1.5 font-mono text-xs text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
                      >
                        {isArmed ? (
                          <ToggleRight className="w-6 h-6 text-[#3FC7D4]" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-[#8A95AA]" />
                        )}
                        <span className={isArmed ? "text-[#3FC7D4] font-bold" : ""}>
                          {isArmed ? "ARMED" : "DISARMED"}
                        </span>
                      </button>

                      <button
                        type="button"
                        disabled={!isArmed || isRunning}
                        onClick={() => handleArmAndExecute(sc)}
                        className={`px-4 py-2 rounded-lg font-mono text-xs font-bold transition-all flex items-center gap-1.5 ${
                          isRunning
                            ? "bg-[#FF4757] text-white animate-pulse"
                            : isArmed
                            ? "bg-[#FF4757]/20 border border-[#FF4757]/40 text-[#FF4757] hover:bg-[#FF4757]/30 shadow-lg"
                            : "bg-[#0B1220] border border-[#3FC7D4]/10 text-[#8A95AA] cursor-not-allowed"
                        }`}
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>{isRunning ? "INJECTING..." : "DISPATCH"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Telemetry & Ingestion Console Output */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 font-mono">
            <div className="flex items-center justify-between text-xs text-[#8A95AA]">
              <span>REPLAY DISPATCH LOG</span>
              <span className="text-[#3FC7D4] animate-pulse">● LIVE</span>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 h-64 overflow-y-auto text-[11px] space-y-1.5 text-[#8A95AA]">
              {statusLog.length > 0 ? (
                statusLog.map((log, idx) => (
                  <div key={idx} className="text-[#E7ECF5] leading-relaxed">
                    {log}
                  </div>
                ))
              ) : (
                <div className="text-[#8A95AA] italic">
                  No replay dispatches logged yet. Arm and trigger a scenario to inject packets into the passive tap.
                </div>
              )}
            </div>

            <div className="pt-2 text-[10px] text-[#8A95AA] space-y-1">
              <div>Telemetry Buffer: <strong className="text-[#3FC7D4]">{alerts.length} alerts</strong></div>
              <div>Active Incidents: <strong className="text-[#FF8A3D]">{incidents.length} correlated</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
