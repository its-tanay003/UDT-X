import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Compass,
  ArrowRight,
  ArrowLeft,
  X,
  Target,
  Sparkles,
  Zap,
  HelpCircle,
} from "lucide-react";
import { useAuthStore } from "../lib/auth";

export interface InteractiveTourStep {
  route: string;
  targetId?: string;
  locationLabel: string;
  title: string;
  summary: string;
  whatIsHere: string[];
  howToUse: string[];
}

export const INTERACTIVE_TOUR_STEPS: InteractiveTourStep[] = [
  {
    route: "/",
    targetId: "tour-rail",
    locationLabel: "LEFT CONSOLE RAIL // SYSTEM WIDE",
    title: "1. Tactical Console Rail & Data Diode Sensor",
    summary:
      "This is your persistent mission-control navigation hub and live hardware telemetry sensor.",
    whatIsHere: [
      "Hardware Data Diode Link Indicator (ONLINE / CONNECTING / THROTTLED)",
      "Instant 1-click access to all 8 operational intelligence consoles",
      "Analyst Identity profile, Settings console, and Station Briefing triggers",
    ],
    howToUse: [
      "Check the top 'DATA DIODE' status to verify one-way RX packet flow.",
      "Switch between consoles at any time with keyboard navigation or direct clicks.",
    ],
  },
  {
    route: "/",
    targetId: "tour-kpis",
    locationLabel: "SECURITY OVERVIEW // TOP METRIC CARDS",
    title: "2. Key Performance Indicators & Ingestion Wire Rates",
    summary:
      "Four real-time instrumentation cards tracking flow bandwidth and escalation volumes.",
    whatIsHere: [
      "Sustained Wire Rate (124,850 EPS benchmark rate vs 7-day Gaussian model)",
      "Active Anomalies (Sessions escalated to the 6 heuristic detection engines)",
      "Kill-Chain Incidents (Graph-correlated multi-stage APT attack chains)",
      "Scored Alerts / Min (100% mapped against MITRE ATT&CK techniques)",
    ],
    howToUse: [
      "Scan these cards first when entering the station to gauge enclave load.",
      "Any red value indicates active hostile penetration requiring priority response.",
    ],
  },
  {
    route: "/",
    targetId: "tour-sphere",
    locationLabel: "SECURITY OVERVIEW // 3D PERIMETER",
    title: "3. 3D Ambient Listening Sphere",
    summary:
      "A real-time WebGL visualization of the one-way inward data-diode enclave thesis.",
    whatIsHere: [
      "Enclave perimeter boundary with host nodes mapped dynamically by severity",
      "Bezier curve arcs connecting actual communicating endpoints",
      "One-way inward particle streams indicating strictly passive, non-intrusive ingestion",
    ],
    howToUse: [
      "Observe ambient node colors: Cyan (Nominal), Amber (High), Red (Critical).",
      "Click 'EXPAND INTERACTIVE GRAPH' to enter 3D orbital inspection mode.",
    ],
  },
  {
    route: "/",
    targetId: "tour-risk-dial",
    locationLabel: "SECURITY OVERVIEW // COMPOSITE POSTURE",
    title: "4. Composite Threat Risk Posture Ring",
    summary:
      "A dynamic 0-100 composite risk rating synthesizing anomaly confidence and asset tiering.",
    whatIsHere: [
      "Real-time composite score calculated across sliding temporal windows",
      "Color-coded operational threat posture (Nominal / Elevated / Critical Alert)",
    ],
    howToUse: [
      "Monitored by commanders to declare containment and escalation states.",
      "Scores above 75 trigger emergency analyst triage and SIEM escalation.",
    ],
  },
  {
    route: "/monitor",
    targetId: "tour-live-table",
    locationLabel: "LIVE MONITOR // TELEMETRY FEED",
    title: "5. Real-Time Telemetry & Alert Stream",
    summary:
      "Zero-refresh streaming table powered by live authenticated WebSockets.",
    whatIsHere: [
      "Filter controls by Threat Class (DDoS, C2, Recon, DGA, TLS, Exfil)",
      "Filter controls by Severity (Critical, High, Medium, Low)",
      "Real-time search bar for IPs, Flow IDs, and Hashes",
    ],
    howToUse: [
      "Filter by 'CRITICAL' to immediately isolate dangerous attacks.",
      "Click 'EVIDENCE →' on any row to open the Explainable AI evidence explorer.",
    ],
  },
  {
    route: "/incidents/INC-2026-0831-01",
    targetId: "tour-incident-timeline",
    locationLabel: "INCIDENT DOSSIER // TEMPORAL GRAPH",
    title: "6. Incident Dossier & Kill-Chain Progression",
    summary:
      "Chronological multi-stage attack chains synthesized across 30-minute rolling graph windows.",
    whatIsHere: [
      "Multi-stage progression timeline (e.g. Recon → C2 Beaconing → Exfiltration)",
      "MITRE ATT&CK technique tags and composite incident severity",
      "Graph Correlation Reasoning explaining why disparate alerts were unified",
    ],
    howToUse: [
      "Follow the numbered stages from top to bottom to trace the attacker's path.",
      "Click 'VIEW INCIDENT IN NEO4J GRAPH CANVAS' to inspect connected graph entities.",
    ],
  },
  {
    route: "/alerts/ALT-001/evidence",
    targetId: "tour-evidence-meters",
    locationLabel: "EVIDENCE EXPLORER // EXPLAINABLE AI",
    title: "7. Evidence Explorer & TreeSHAP Attributions",
    summary:
      "Full transparency into machine learning and heuristic detection decisions.",
    whatIsHere: [
      "Statistical Evidence Meters (Shannon entropy, SYN/ACK ratios, IAT variance)",
      "Signed TreeSHAP Feature Attributions showing exact mathematical contributions",
      "Confidence percentage and classification rationale",
    ],
    howToUse: [
      "Inspect the green and red TreeSHAP bars to see why the AI flagged the event.",
      "Verify statistical threshold crossings before initiating firewall or SOC action.",
    ],
  },
  {
    route: "/graph",
    targetId: "tour-graph-canvas",
    locationLabel: "NETWORK GRAPH // 3D ORBITAL CANVAS",
    title: "8. Interactive 3D Evidence Graph & Node Inspector",
    summary:
      "Full-screen 3D orbital canvas with interactive node interrogation and Neo4j links.",
    whatIsHere: [
      "Orbit / Pan / Zoom 3D camera controls with Bloom lighting passes",
      "Interactive Host Nodes clickable for live forensic inspection",
      "Right-hand Node Telemetry Inspector showing connected flow arcs and risk ratings",
    ],
    howToUse: [
      "Drag with mouse to rotate the sphere; scroll wheel to zoom into specific clusters.",
      "Click any host sphere to view its IP, severity level, and active attack edges.",
    ],
  },
  {
    route: "/threats",
    targetId: "tour-sonar-chart",
    locationLabel: "THREAT CENTER // D3 RADAR SWEEP",
    title: "9. Threat Center & D3 Radial Sonar Sweep",
    summary:
      "Polar coordinate sonar visualization mapping threat distributions and severity wedges.",
    whatIsHere: [
      "Concentric sonar rings (25%, 50%, 75%, 100%)",
      "Interactive polar wedge arcs sized by alert volume and colored by risk score",
      "Forensic profile drilldown pane and historical time filters (1h, 24h, 7d, 30d)",
    ],
    howToUse: [
      "Click any wedge segment to inspect specific class metrics (e.g. DDoS vs C2).",
      "Toggle time filters in the top right to analyze weekly or monthly baselines.",
    ],
  },
  {
    route: "/replay",
    targetId: "tour-replay-console",
    locationLabel: "REPLAY LAB // ATTACK SIMULATOR",
    title: "10. Replay Lab Scenario Simulator",
    summary:
      "Hardware-isolated simulation console with physical-style toggle switches for live demonstrations.",
    whatIsHere: [
      "Pre-configured scenarios: Multi-Stage APT, DDoS Flood, DGA C2, Exfil Spike",
      "Physical interface safety isolation guard (prevents non-loopback transmission)",
      "Live trigger buttons that inject real synthetic telemetry into the pipeline",
    ],
    howToUse: [
      "Click 'RUN SIMULATION' on the 'Multi-Stage APT Kill-Chain' preset.",
      "Watch alerts propagate in real-time across the Live Monitor, Sphere, and Dossier.",
    ],
  },
  {
    route: "/performance",
    targetId: "tour-perf-charts",
    locationLabel: "PERFORMANCE // SLA METRICS",
    title: "11. SLA Telemetry & Latency Percentiles",
    summary:
      "Sub-second performance monitoring proving the platform's high-throughput capability.",
    whatIsHere: [
      "P99 Pipeline Latency (< 5.0 ms SLA target verification)",
      "Real-time event throughput area charts (benchmarked at 124,850 EPS)",
      "Cluster CPU usage and Kafka consumer group lag (0 ms backpressure)",
    ],
    howToUse: [
      "Verify that P99 latency remains under 10ms during heavy simulated traffic.",
      "Demonstrate platform scalability and zero-loss packet processing to reviewers.",
    ],
  },
  {
    route: "/settings",
    targetId: "tour-settings-panel",
    locationLabel: "STATION SETTINGS // PREFERENCES",
    title: "12. Server-Persisted Settings & Accessibility",
    summary:
      "Configure your personal station preferences and export configurations.",
    whatIsHere: [
      "Alert audio ping rules and notification threshold dropdowns",
      "3D Listening Sphere particle density selector (High / Low / Off for low-end GPUs)",
      "Default SIEM export formats (CEF / Syslog / STIX)",
    ],
    howToUse: [
      "Adjust particle density if your machine requires GPU workload reduction.",
      "All settings save automatically to the backend server and follow your account.",
    ],
  },
];

export const TourGuide: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    tourActive,
    tourStepIndex,
    nextTourStep,
    prevTourStep,
    skipTour,
    completeTour,
  } = useAuthStore();

  const currentStep = INTERACTIVE_TOUR_STEPS[tourStepIndex] || INTERACTIVE_TOUR_STEPS[0];
  const isLast = tourStepIndex === INTERACTIVE_TOUR_STEPS.length - 1;
  const isFirst = tourStepIndex === 0;

  // Auto-navigate to the step's designated route so the user sees the real page
  useEffect(() => {
    if (tourActive && currentStep && location.pathname !== currentStep.route) {
      navigate(currentStep.route);
    }
  }, [tourActive, tourStepIndex, currentStep, location.pathname, navigate]);

  if (!tourActive) return null;

  return (
    <div className="fixed inset-0 z-50 pointer-events-none select-none font-mono">
      {/* Ambient Tactical Dark Dimmer */}
      <div className="absolute inset-0 bg-[#0B1220]/75 backdrop-blur-[2px] pointer-events-auto" />

      {/* Floating Comprehensive Tactical Station Guide Panel */}
      <div className="absolute bottom-6 right-6 w-full max-w-xl p-6 rounded-2xl bg-[#131B2E] border-2 border-[#3FC7D4] shadow-[0_0_50px_rgba(63,199,212,0.25)] space-y-4 pointer-events-auto max-h-[90vh] overflow-y-auto">
        {/* Header Ribbon */}
        <div className="flex items-center justify-between pb-3 border-b border-[#3FC7D4]/20">
          <div className="flex items-center gap-2 text-xs font-bold text-[#3FC7D4]">
            <Compass className="w-4 h-4 animate-spin" />
            <span className="tracking-widest">
              STATION OPERATIONAL TOUR // STEP {String(tourStepIndex + 1).padStart(2, "0")} / {String(INTERACTIVE_TOUR_STEPS.length).padStart(2, "0")}
            </span>
          </div>
          <button
            onClick={skipTour}
            className="p-1 rounded text-[#8A95AA] hover:text-[#E7ECF5] hover:bg-[#0B1220] transition-colors"
            title="Dismiss Tour"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Location & Title */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] text-[#3FC7D4] font-bold uppercase tracking-wider">
            <Target className="w-3 h-3 animate-pulse text-[#FF8A3D]" />
            <span>{currentStep.locationLabel}</span>
          </div>
          <h2 className="font-display text-lg font-bold text-[#E7ECF5] tracking-tight">
            {currentStep.title}
          </h2>
          <p className="text-xs text-[#8A95AA] leading-relaxed">
            {currentStep.summary}
          </p>
        </div>

        {/* Section 1: What is on this screen? */}
        <div className="p-3.5 rounded-xl bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#E7ECF5] uppercase">
            <Sparkles className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>What is located here:</span>
          </div>
          <ul className="space-y-1.5 text-[11px] text-[#8A95AA]">
            {currentStep.whatIsHere.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#3FC7D4] mt-0.5">▸</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Section 2: How do you use it? */}
        <div className="p-3.5 rounded-xl bg-[#0B1220] border border-[#FF8A3D]/20 space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#E7ECF5] uppercase">
            <Zap className="w-3.5 h-3.5 text-[#FF8A3D]" />
            <span>How to use this component:</span>
          </div>
          <ul className="space-y-1.5 text-[11px] text-[#8A95AA]">
            {currentStep.howToUse.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#FF8A3D] mt-0.5">✓</span>
                <span className="text-[#E7ECF5]">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Navigation Actions Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-[#3FC7D4]/15 text-xs">
          <button
            onClick={skipTour}
            className="text-[11px] text-[#8A95AA] hover:text-[#E7ECF5] hover:underline"
          >
            DISMISS BRIEFING
          </button>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                onClick={prevTourStep}
                className="px-3.5 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/30 text-[#8A95AA] hover:text-[#E7ECF5] flex items-center gap-1.5 font-bold transition-all"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                PREV
              </button>
            )}

            <button
              onClick={isLast ? completeTour : nextTourStep}
              className="px-5 py-2 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold hover:bg-[#35B2BE] transition-all flex items-center gap-1.5 shadow-[0_0_15px_rgba(63,199,212,0.3)]"
            >
              <span>{isLast ? "COMPLETE STATION TOUR" : "NEXT STEP"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
