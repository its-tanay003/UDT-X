import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Compass,
  Database,
  Flame,
  Globe,
  Radio,
  RefreshCw,
  Search,
  Settings,
  Shield,
  User,
  Zap,
} from "lucide-react";
import { useLiveStore } from "./lib/store";
import { useAuthStore } from "./lib/auth";
import { LoginPage } from "./pages/Login";
import { OverviewPage } from "./pages/Overview";
import { LiveMonitorPage } from "./pages/LiveMonitor";
import { IncidentDetailPage } from "./pages/IncidentDetail";
import { EvidenceExplorerPage } from "./pages/EvidenceExplorer";
import { NetworkGraphPage } from "./pages/NetworkGraph";
import { ThreatCenterPage } from "./pages/ThreatCenter";
import { ReplayLabPage } from "./pages/ReplayLab";
import { PerformancePage } from "./pages/Performance";
import { ProfilePage } from "./pages/Profile";
import { SettingsPage } from "./pages/Settings";
import { BootSequence } from "./components/BootSequence";
import { TourGuide } from "./components/TourGuide";

const ConsoleRail: React.FC = () => {
  const { isConnected, isConnecting } = useLiveStore();
  const { user, isThrottled, startTour } = useAuthStore();

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
    <aside id="tour-rail" className="w-64 bg-[#0B1220] border-r border-[#3FC7D4]/15 flex flex-col justify-between shrink-0 p-4 select-none">
      <div className="space-y-5">
        {/* Enclave Brand & Header */}
        <div id="tour-rail-brand" className="flex items-center gap-3 px-2 py-1">
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
        <div id="tour-diode-box" className="p-3 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-[#8A95AA]">DATA DIODE:</span>
            <span
              className={`font-bold flex items-center gap-1.5 ${
                isThrottled
                  ? "text-[#FF8A3D]"
                  : isConnected
                  ? "text-[#4CAF7D]"
                  : isConnecting
                  ? "text-[#FF8A3D]"
                  : "text-[#8A95AA]"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isThrottled
                    ? "bg-[#FF8A3D] animate-ping"
                    : isConnected
                    ? "bg-[#4CAF7D] animate-pulse"
                    : isConnecting
                    ? "bg-[#FF8A3D] animate-ping"
                    : "bg-[#8A95AA]"
                }`}
              />
              {isThrottled ? "THROTTLED" : isConnected ? "ONLINE" : isConnecting ? "CONNECTING" : "LISTENING"}
            </span>
          </div>
          <div className="text-[10px] font-mono text-[#8A95AA]">
            Direction: <strong className="text-[#3FC7D4]">INWARD ONLY (PASSIVE)</strong>
          </div>
        </div>

        {/* Navigation Rail Links */}
        <nav id="tour-nav-links" className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                id={`tour-nav-${item.label.toLowerCase().replace(/[\s-]+/g, "_")}`}
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-mono transition-all ${
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

      {/* Account & Tour Utilities */}
      <div id="tour-user-profile" className="pt-3 border-t border-[#3FC7D4]/10 space-y-1 font-mono text-xs">
        <NavLink
          to="/profile"
          id="tour-nav-profile"
          className={({ isActive }) =>
            `w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[11px] transition-colors ${
              isActive ? "bg-[#1B2540] text-[#3FC7D4] font-bold" : "text-[#8A95AA] hover:text-[#E7ECF5]"
            }`
          }
        >
          <User className="w-3.5 h-3.5" />
          <span>{user?.display_name || "Profile"}</span>
        </NavLink>

        <NavLink
          to="/settings"
          id="tour-nav-settings"
          className={({ isActive }) =>
            `w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[11px] transition-colors ${
              isActive ? "bg-[#1B2540] text-[#3FC7D4] font-bold" : "text-[#8A95AA] hover:text-[#E7ECF5]"
            }`
          }
        >
          <Settings className="w-3.5 h-3.5" />
          <span>Settings</span>
        </NavLink>

        <button
          onClick={startTour}
          id="tour-nav-briefing-btn"
          className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[11px] text-[#3FC7D4] hover:bg-[#131B2E] transition-colors text-left"
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Station Briefing</span>
        </button>

        <div className="pt-2 text-[10px] text-[#8A95AA] flex justify-between">
          <span>AIR-GAPPED</span>
          <span className="text-[#3FC7D4]">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};

export const App: React.FC = () => {
  const { user, isThrottled, throttleSeconds } = useAuthStore();
  const { connectWebSocket } = useLiveStore();
  const [isBooting, setIsBooting] = useState(false);

  useEffect(() => {
    // Open authenticated WebSocket with JWT token
    const token = useAuthStore.getState().accessToken;
    const wsUrl = token
      ? `ws://localhost:8000/ws/live?token=${token}`
      : "ws://localhost:8000/ws/live";

    const cleanup = connectWebSocket(wsUrl, "http://localhost:8000");
    return cleanup;
  }, [connectWebSocket, user]);

  // If user is not authenticated, render Login Page
  if (!user) {
    return <LoginPage onSuccess={() => setIsBooting(true)} />;
  }

  // If boot sequence is active on login, render BootSequence
  if (isBooting) {
    return <BootSequence onComplete={() => setIsBooting(false)} />;
  }

  return (
    <BrowserRouter>
      <div className="w-screen h-screen bg-[#0B1220] text-[#E7ECF5] flex overflow-hidden font-sans relative">
        {/* Rate Limiting Toast Notification */}
        {isThrottled && (
          <div className="absolute top-4 right-4 z-50 p-4 rounded-xl bg-[#131B2E] border border-[#FF8A3D] shadow-2xl flex items-center gap-3 font-mono text-xs text-[#FF8A3D] animate-bounce">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <div className="font-bold">TRANSMISSION THROTTLED (HTTP 429)</div>
              <div className="text-[10px] text-[#8A95AA]">
                Resuming in <span className="text-[#FF8A3D] font-bold">{throttleSeconds}s</span>...
              </div>
            </div>
          </div>
        )}

        {/* Tour Guide Spotlight Overlay */}
        <TourGuide />

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
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            {/* Fallback */}
            <Route path="*" element={<OverviewPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
