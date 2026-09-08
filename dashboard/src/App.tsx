import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bot,
  Compass,
  Database,
  Flame,
  Globe,
  Menu,
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
import { Tooltip } from "./components/Tooltip";
import { LoginPage } from "./pages/Login";
import { OverviewPage } from "./pages/Overview";
import { LiveMonitorPage } from "./pages/LiveMonitor";
import { IncidentsPage } from "./pages/Incidents";
import { AlertsPage } from "./pages/Alerts";
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
import { ExperiencePrompt } from "./components/ExperiencePrompt";
import { CopilotModal } from "./components/CopilotModal";

interface ConsoleRailProps {
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

const ConsoleRail: React.FC<ConsoleRailProps> = ({ isMobileOpen, setIsMobileOpen }) => {
  const { isConnected, isConnecting } = useLiveStore();
  const { user, isThrottled, startTour } = useAuthStore();

  const navItems = [
    { to: "/", label: "OVERVIEW", icon: Shield, tip: "Security Command Center & Enclave Status" },
    { to: "/monitor", label: "LIVE MONITOR", icon: Radio, tip: "Real-time Telemetry & Anomaly Stream" },
    { to: "/alerts", label: "ALERTS FEED", icon: Search, tip: "Comprehensive Anomaly Index & SIEM Export" },
    { to: "/incidents", label: "INCIDENT DOSSIER", icon: Flame, tip: "Correlated Multi-stage Attack Chains" },
    { to: "/graph", label: "NETWORK GRAPH", icon: Globe, tip: "3D Passive Tap & Topology Canvas" },
    { to: "/threats", label: "THREAT CENTER", icon: Zap, tip: "Radial Sonar Threat Matrix & Analytics" },
    { to: "/replay", label: "REPLAY LAB", icon: RefreshCw, tip: "Hardware-Guarded Attack Scenario Simulator" },
    { to: "/performance", label: "PERFORMANCE", icon: Activity, tip: "Sub-5ms SLA & Wire Rate Telemetry" },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 bg-[#0B1220]/80 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      <aside
        id="tour-rail"
        className={`
          fixed md:static inset-y-0 left-0 z-50
          transition-all duration-300 ease-in-out
          ${isMobileOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0 w-16 lg:w-64"}
          bg-[#0B1220] border-r border-[#3FC7D4]/15 flex flex-col justify-between shrink-0 p-3 lg:p-4 select-none
        `}
      >
        <div className="space-y-4 lg:space-y-5">
          {/* Enclave Brand & Header */}
          <div id="tour-rail-brand" className="flex items-center gap-3 px-1.5 lg:px-2 py-1">
            <div className="w-8 h-8 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center shrink-0">
              <Shield className="w-4 h-4 text-[#3FC7D4]" />
            </div>
            <div className={`overflow-hidden transition-opacity ${!isMobileOpen ? "hidden lg:block" : "block"}`}>
              <div className="font-display font-bold text-sm tracking-wider text-[#E7ECF5] whitespace-nowrap">
                UDT-X ENCLAVE
              </div>
              <div className="text-[10px] font-mono text-[#8A95AA] whitespace-nowrap">
                SIGINT LISTENING POST
              </div>
            </div>
          </div>

          {/* Data Diode Status Box */}
          <div id="tour-diode-box" className="p-2 lg:p-3 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className={`text-[#8A95AA] ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>DATA DIODE:</span>
              <span
                className={`font-bold flex items-center gap-1.5 mx-auto lg:mx-0 ${
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
                <span className={!isMobileOpen ? "hidden lg:inline" : "inline"}>
                  {isThrottled ? "THROTTLED" : isConnected ? "ONLINE" : isConnecting ? "CONNECTING" : "LISTENING"}
                </span>
              </span>
            </div>
            <div className={`text-[10px] font-mono text-[#8A95AA] ${!isMobileOpen ? "hidden lg:block" : "block"}`}>
              Direction: <strong className="text-[#3FC7D4]">INWARD ONLY</strong>
            </div>
          </div>

          {/* Navigation Rail Links */}
          <nav id="tour-nav-links" className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Tooltip key={item.to} content={item.tip} position="right" className="w-full">
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    onClick={() => setIsMobileOpen(false)}
                    id={`tour-nav-${item.label.toLowerCase().replace(/[\s-]+/g, "_")}`}
                    className={({ isActive }) =>
                      `w-full flex items-center gap-3 px-2.5 lg:px-3 py-2 rounded-lg text-xs font-mono transition-all ${
                        isActive
                          ? "bg-[#1B2540] text-[#3FC7D4] border-l-2 border-[#3FC7D4] font-bold shadow-[inset_0_0_12px_rgba(63,199,212,0.1)]"
                          : "text-[#8A95AA] hover:bg-[#131B2E] hover:text-[#E7ECF5]"
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0 mx-auto lg:mx-0" />
                    <span className={`truncate ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>{item.label}</span>
                  </NavLink>
                </Tooltip>
              );
            })}
          </nav>
        </div>

        {/* Account & Tour Utilities */}
        <div id="tour-user-profile" className="pt-3 border-t border-[#3FC7D4]/10 space-y-1 font-mono text-xs">
          <Tooltip content="Operator Clearances & Active Session" position="right" className="w-full">
            <NavLink
              to="/profile"
              onClick={() => setIsMobileOpen(false)}
              id="tour-nav-profile"
              className={({ isActive }) =>
                `w-full flex items-center gap-2.5 px-2.5 lg:px-3 py-1.5 rounded-lg text-[11px] transition-colors ${
                  isActive ? "bg-[#1B2540] text-[#3FC7D4] font-bold" : "text-[#8A95AA] hover:text-[#E7ECF5]"
                }`
              }
            >
              <User className="w-3.5 h-3.5 shrink-0 mx-auto lg:mx-0" />
              <span className={`truncate ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>{user?.display_name || "Profile"}</span>
            </NavLink>
          </Tooltip>

          <Tooltip content="Detection Thresholds & Particle Preferences" position="right" className="w-full">
            <NavLink
              to="/settings"
              onClick={() => setIsMobileOpen(false)}
              id="tour-nav-settings"
              className={({ isActive }) =>
                `w-full flex items-center gap-2.5 px-2.5 lg:px-3 py-1.5 rounded-lg text-[11px] transition-colors ${
                  isActive ? "bg-[#1B2540] text-[#3FC7D4] font-bold" : "text-[#8A95AA] hover:text-[#E7ECF5]"
                }`
              }
            >
              <Settings className="w-3.5 h-3.5 shrink-0 mx-auto lg:mx-0" />
              <span className={`truncate ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>Settings</span>
            </NavLink>
          </Tooltip>

          <Tooltip content="AI-Native Enclave Copilot (Ctrl + K)" position="right" className="w-full">
            <button
              onClick={() => {
                setIsMobileOpen(false);
                window.dispatchEvent(new CustomEvent("open-udtx-copilot"));
              }}
              id="tour-nav-copilot-btn"
              className="w-full flex items-center gap-2.5 px-2.5 lg:px-3 py-2 rounded-lg text-xs font-mono font-bold bg-[#3FC7D4]/10 hover:bg-[#3FC7D4]/20 border border-[#3FC7D4]/30 text-[#3FC7D4] transition-all text-left group shadow-[0_0_12px_rgba(63,199,212,0.15)] active:scale-[0.97]"
            >
              <Bot className="w-4 h-4 shrink-0 mx-auto lg:mx-0 animate-pulse text-[#3FC7D4]" />
              <span className={`truncate ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>SENTINEL COPILOT</span>
              <span className={`ml-auto text-[9px] px-1.5 py-0.5 rounded bg-[#0B1220] border border-[#3FC7D4]/30 text-[#8A95AA] ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>^K</span>
            </button>
          </Tooltip>

          <Tooltip content="Interactive 14-Step Station Onboarding" position="right" className="w-full">
            <button
              onClick={() => {
                setIsMobileOpen(false);
                startTour();
              }}
              id="tour-nav-briefing-btn"
              className="w-full flex items-center gap-2.5 px-2.5 lg:px-3 py-1.5 rounded-lg text-[11px] text-[#3FC7D4] hover:bg-[#131B2E] transition-colors text-left"
            >
              <Compass className="w-3.5 h-3.5 shrink-0 mx-auto lg:mx-0" />
              <span className={`truncate ${!isMobileOpen ? "hidden lg:inline" : "inline"}`}>Station Briefing</span>
            </button>
          </Tooltip>

          <div className={`pt-2 text-[10px] text-[#8A95AA] justify-between ${!isMobileOpen ? "hidden lg:flex" : "flex"}`}>
            <span>AIR-GAPPED</span>
            <span className="text-[#3FC7D4]">v1.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
};

import { motion, AnimatePresence } from "framer-motion";

const AnimatedRoutes: React.FC = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="w-full"
      >
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/monitor" element={<LiveMonitorPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
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
      </motion.div>
    </AnimatePresence>
  );
};

export const App: React.FC = () => {
  const { user, isThrottled, throttleSeconds } = useAuthStore();
  const { connectWebSocket } = useLiveStore();
  const [isBooting, setIsBooting] = useState(false);
  const [showExperiencePrompt, setShowExperiencePrompt] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCopilotOpen((prev) => !prev);
      }
    };
    const handleCustomOpen = () => setIsCopilotOpen(true);

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("open-udtx-copilot", handleCustomOpen);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("open-udtx-copilot", handleCustomOpen);
    };
  }, []);

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
    return (
      <LoginPage
        onSuccess={() => {
          setIsBooting(true);
        }}
      />
    );
  }

  // If boot sequence is active on login, render BootSequence
  if (isBooting) {
    return (
      <BootSequence
        onComplete={() => {
          setIsBooting(false);
          setShowExperiencePrompt(true);
        }}
      />
    );
  }

  // If user has not yet cleared experience gate, render ExperiencePrompt
  if (showExperiencePrompt) {
    return (
      <ExperiencePrompt
        onComplete={() => {
          setShowExperiencePrompt(false);
        }}
      />
    );
  }

  return (
    <BrowserRouter>
      <div className="w-screen h-screen bg-[#0B1220] text-[#E7ECF5] flex flex-col md:flex-row overflow-hidden font-sans relative">
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

        {/* Mobile Top Navigation Bar (Hidden on md+) */}
        <div className="md:hidden w-full bg-[#0B1220] border-b border-[#3FC7D4]/15 px-4 py-3 flex items-center justify-between shrink-0 z-30">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
              className="p-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/30 text-[#3FC7D4] hover:bg-[#1B2540] transition-colors"
              aria-label="Toggle Station Menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#3FC7D4]" />
              <span className="font-display font-bold text-sm tracking-wider text-[#E7ECF5]">
                UDT-X ENCLAVE
              </span>
            </div>
          </div>

          <div className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#131B2E] border border-[#3FC7D4]/25 text-[#3FC7D4] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4CAF7D] animate-pulse" />
            <span>AIR-GAPPED</span>
          </div>
        </div>

        {/* Tour Guide Spotlight Overlay */}
        <TourGuide />

        {/* Left Console Rail Navigation */}
        <ConsoleRail
          isMobileOpen={isMobileNavOpen}
          setIsMobileOpen={setIsMobileNavOpen}
        />

        {/* Main Mission Control Screen Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-5 lg:p-6 relative min-w-0">
          <AnimatedRoutes />
        </main>

        {/* Interactive 14-Step Station Tour */}
        <TourGuide />

        {/* AI-Native Sentinel Copilot Modal */}
        <CopilotModal isOpen={isCopilotOpen} onClose={() => setIsCopilotOpen(false)} />
      </div>
    </BrowserRouter>
  );
};

export default App;
