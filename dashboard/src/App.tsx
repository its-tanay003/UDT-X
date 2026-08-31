import React, { useEffect, useState } from "react";
import {
  Activity,
  BarChart2,
  Cpu,
  Flame,
  Globe,
  Layers,
  Lock,
  Network,
  Radio,
  Shield,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";
import { useLiveStore } from "./lib/store";
import { OverviewPage } from "./pages/Overview";
import { LiveMonitorPage } from "./pages/LiveMonitor";
import { IncidentDetailPage } from "./pages/IncidentDetail";
import { EvidenceExplorerPage } from "./pages/EvidenceExplorer";
import { NetworkGraphPage } from "./pages/NetworkGraph";
import { ThreatCenterPage } from "./pages/ThreatCenter";
import { ReplayLabPage } from "./pages/ReplayLab";
import { PerformancePage } from "./pages/Performance";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>("INC-20260827-01");
  const [selectedAlertId, setSelectedAlertId] = useState<string>("ALT-EXFIL-003");

  const { isConnected, connectWebSocket } = useLiveStore();

  useEffect(() => {
    const disconnect = connectWebSocket("ws://localhost:8000/ws/live");
    return () => disconnect();
  }, [connectWebSocket]);

  const navItems = [
    { id: "overview", label: "Security Overview", icon: Shield },
    { id: "live", label: "Live Monitor", icon: Activity },
    { id: "incident", label: "Incident Dossier", icon: Flame },
    { id: "evidence", label: "Evidence Explorer", icon: ShieldAlert },
    { id: "graph", label: "Network Graph", icon: Network },
    { id: "threats", label: "Threat Center", icon: BarChart2 },
    { id: "replay", label: "Replay Lab (SIH Demo)", icon: Sparkles },
    { id: "performance", label: "Performance", icon: Cpu },
  ];

  return (
    <div className="min-h-screen bg-[#0B1220] flex text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220]">
      {/* Left Console Rail Navigation (Mission-Control Shell) */}
      <aside className="w-64 border-r border-[#3FC7D4]/15 bg-[#0B1220]/95 backdrop-blur-xl flex flex-col justify-between p-4 sticky top-0 h-screen z-50">
        <div className="space-y-6">
          {/* Station Brand Title */}
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/30 text-[#3FC7D4] shadow-[0_0_12px_rgba(63,199,212,0.2)]">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="font-display font-bold text-sm tracking-wider text-[#E7ECF5]">
                UDT-X // DEFENSE
              </div>
              <div className="text-[10px] font-mono text-[#8A95AA] uppercase tracking-widest">
                Passive Station v1.0
              </div>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1 font-mono text-xs">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-left transition-all ${
                    isActive
                      ? "bg-[#131B2E] text-[#3FC7D4] border border-[#3FC7D4]/40 shadow-[0_0_12px_rgba(63,199,212,0.15)] font-bold"
                      : "text-[#8A95AA] hover:text-[#E7ECF5] hover:bg-[#131B2E]/50"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#3FC7D4]" : "text-[#8A95AA]"}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Persistent Console Status Footer */}
        <div className="p-3.5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#8A95AA] uppercase">DATA DIODE LINK</span>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-[#4CAF7D] animate-pulse" : "bg-[#3FC7D4] animate-ping"
                }`}
              />
              <span className="text-[11px] font-bold text-[#E7ECF5]">
                {isConnected ? "ONLINE" : "LISTENING"}
              </span>
            </div>
          </div>
          <div className="text-[10px] text-[#8A95AA] leading-relaxed">
            One-Way Optical Ingress // Zero Return Path
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl">
        {activeTab === "overview" && (
          <OverviewPage onNavigate={(t) => setActiveTab(t)} />
        )}
        {activeTab === "live" && (
          <LiveMonitorPage
            onSelectAlert={(id) => {
              setSelectedAlertId(id);
              setActiveTab("evidence");
            }}
            onSelectIncident={(id) => {
              setSelectedIncidentId(id);
              setActiveTab("incident");
            }}
          />
        )}
        {activeTab === "incident" && (
          <IncidentDetailPage
            incidentId={selectedIncidentId}
            onBack={() => setActiveTab("overview")}
            onSelectAlert={(id) => {
              setSelectedAlertId(id);
              setActiveTab("evidence");
            }}
            onNavigateGraph={() => setActiveTab("graph")}
          />
        )}
        {activeTab === "evidence" && (
          <EvidenceExplorerPage
            alertId={selectedAlertId}
            onBack={() => setActiveTab("live")}
          />
        )}
        {activeTab === "graph" && (
          <NetworkGraphPage
            onBack={() => setActiveTab("overview")}
            onSelectAlert={(id) => {
              setSelectedAlertId(id);
              setActiveTab("evidence");
            }}
          />
        )}
        {activeTab === "threats" && (
          <ThreatCenterPage
            onBack={() => setActiveTab("overview")}
            onSelectThreat={() => setActiveTab("live")}
          />
        )}
        {activeTab === "replay" && (
          <ReplayLabPage
            onBack={() => setActiveTab("overview")}
            onSelectAlert={(id) => {
              setSelectedAlertId(id);
              setActiveTab("evidence");
            }}
          />
        )}
        {activeTab === "performance" && (
          <PerformancePage onBack={() => setActiveTab("overview")} />
        )}
      </main>
    </div>
  );
}

export default App;
