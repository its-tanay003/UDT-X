import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import {
  Activity,
  AlertCircle,
  Database,
  Flame,
  Globe,
  Radio,
  RefreshCw,
  Search,
  Shield,
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

const ConsoleRail: React.FC = () => {
  const { isConnected, isConnecting } = useLiveStore();

  const navItems = [
    { to: "/", label: "OVERVIEW", icon: Shield },
    { to: "/monitor", label: "LIVE MONITOR", icon: Radio },
    { to: "/incidents/INC-2026-0831-01", label: "INCIDENT DOSSIER", icon: Flame },
    { to: "/alerts/ALT-001/evidence", label: "EVIDENCE EXPLORER", icon: Search },
    { to: "/graph", label: "NETWORK GRAPH", icon: Globe },
    { to: "/threats", label: "THREAT CENTER", icon: Zap },
    { to: "/replay", label: "REPLAY LAB", icon: RefreshCw },
    { to: "/performance", label: "PERFORMANCE", icon: Activity },
  ];

  return (
    <aside className="w-64 bg-[#0B1220] border-r border-[#3FC7D4]/15 flex flex-col justify-between shrink-0 p-4 select-none">
      <div className="space-y-6">
        {/* Enclave Brand & Header */}
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="w-8 h-8 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center">
            <Shield className="w-4 h-4 text-[#3FC7D4]" />
          </div>
          <div>
            <div className="font-display font-bold text-sm tracking-wider text-[#E7ECF5]">
              UDT-X ENCLAVE
            </div>
            <div className="text-[10px] font-mono text-[#8A95AA]">
              SIGINT LISTENING POST
            </div>
          </div>
        </div>

        {/* Data Diode Status Box */}
        <div className="p-3 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-[#8A95AA]">DATA DIODE:</span>
            <span
              className={`font-bold flex items-center gap-1.5 ${
                isConnected
                  ? "text-[#4CAF7D]"
                  : isConnecting
                  ? "text-[#FF8A3D]"
                  : "text-[#8A95AA]"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected
                    ? "bg-[#4CAF7D] animate-pulse"
                    : isConnecting
                    ? "bg-[#FF8A3D] animate-ping"
                    : "bg-[#8A95AA]"
                }`}
              />
              {isConnected ? "ONLINE" : isConnecting ? "CONNECTING" : "LISTENING"}
            </span>
          </div>
          <div className="text-[10px] font-mono text-[#8A95AA]">
            Direction: <strong className="text-[#3FC7D4]">INWARD ONLY (PASSIVE)</strong>
          </div>
        </div>

        {/* Navigation Rail Links */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-mono transition-all ${
                    isActive
                      ? "bg-[#1B2540] text-[#3FC7D4] border-l-2 border-[#3FC7D4] font-bold shadow-[inset_0_0_12px_rgba(63,199,212,0.1)]"
                      : "text-[#8A95AA] hover:bg-[#131B2E] hover:text-[#E7ECF5]"
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Telemetry */}
      <div className="pt-4 border-t border-[#3FC7D4]/10 text-[10px] font-mono text-[#8A95AA] space-y-1">
        <div className="flex justify-between">
          <span>PIPELINE:</span>
          <span className="text-[#3FC7D4]">v1.0.0 PROD</span>
        </div>
        <div className="flex justify-between">
          <span>ENCLAVE:</span>
          <span className="text-[#E7ECF5]">AIR-GAPPED</span>
        </div>
      </div>
    </aside>
  );
};

export const App: React.FC = () => {
  const { connectWebSocket } = useLiveStore();

  useEffect(() => {
    // Open WebSocket once on mount with auto-reconnect and REST hydration
    const cleanup = connectWebSocket("ws://localhost:8000/ws/live", "http://localhost:8000");
    return cleanup;
  }, [connectWebSocket]);

  return (
    <BrowserRouter>
      <div className="w-screen h-screen bg-[#0B1220] text-[#E7ECF5] flex overflow-hidden font-sans">
        {/* Left Console Rail Navigation */}
        <ConsoleRail />

        {/* Main Mission Control Screen Area */}
        <main className="flex-1 overflow-y-auto p-6 relative">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/monitor" element={<LiveMonitorPage />} />
            <Route path="/incidents/:id" element={<IncidentDetailPage />} />
            <Route path="/alerts/:id/evidence" element={<EvidenceExplorerPage />} />
            <Route path="/graph" element={<NetworkGraphPage />} />
            <Route path="/threats" element={<ThreatCenterPage />} />
            <Route path="/replay" element={<ReplayLabPage />} />
            <Route path="/performance" element={<PerformancePage />} />
            {/* Fallback */}
            <Route path="*" element={<OverviewPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
