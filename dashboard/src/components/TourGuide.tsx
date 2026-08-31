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
  Layers,
  Search,
  Activity,
  Flame,
  Radio,
  Globe,
  Settings,
  HelpCircle,
} from "lucide-react";
import { useAuthStore } from "../lib/auth";

export interface InteractiveTourStep {
  route: string;
  targetId: string;
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
    locationLabel: "LEFT CONSOLE RAIL // PERSISTENT NAVIGATION",
    title: "1. Tactical Console Rail & Data Diode Sensor",
    summary:
      "Your persistent mission-control sidebar and live physical sensor state monitor.",
    whatIsHere: [
      "Hardware Data Diode Link Box (ONLINE / CONNECTING / THROTTLED)",
      "Instant 1-click access to all 8 operational intelligence consoles",
      "Operator Profile, Settings, and manual Station Briefing re-launch trigger",
    ],
    howToUse: [
      "Check the top 'DATA DIODE' status to verify one-way RX packet flow.",
      "Click any console link or use keyboard navigation to switch screens instantaneously.",
    ],
  },
  {
    route: "/",
    targetId: "tour-kpis",
    locationLabel: "SECURITY OVERVIEW // TOP METRIC CARDS",
    title: "2. Key Performance Indicators & Ingestion Wire Rates",
    summary:
      "Four real-time instrumentation cards tracking network flow rates and threat escalations.",
    whatIsHere: [
      "Sustained Wire Rate (124,850 EPS benchmark vs 7-day Gaussian model)",
      "Active Anomalies (Sessions escalated to the 6 heuristic detection engines)",
      "Kill-Chain Incidents (Graph-correlated multi-stage APT attack chains)",
      "Scored Alerts / Min (100% mapped against MITRE ATT&CK techniques)",
    ],
    howToUse: [
      "Scan these cards first when entering the station to gauge enclave load.",
      "Red or Amber values indicate active intrusions requiring priority investigation.",
    ],
  },
  {
    route: "/",
    targetId: "tour-sphere-panel",
    locationLabel: "SECURITY OVERVIEW // 3D PERIMETER",
    title: "3. 3D Ambient Listening Sphere",
    summary:
      "A real-time WebGL visualization of the one-way inward data-diode enclave architecture.",
    whatIsHere: [
      "Perimeter sphere boundary with host nodes mapped dynamically by severity",
      "Bezier curve arcs connecting actual communicating endpoints",
      "One-way inward particle streams indicating strictly passive, non-intrusive ingestion",
    ],
    howToUse: [
      "Observe ambient node colors: Cyan (Nominal), Amber (High), Red (Critical).",
      "Click 'EXPAND INTERACTIVE GRAPH →' to enter the dedicated full-screen 3D inspection console.",
    ],
  },
  {
    route: "/",
    targetId: "tour-risk-panel",
    locationLabel: "SECURITY OVERVIEW // COMPOSITE POSTURE",
    title: "4. Composite Threat Risk Posture Ring",
    summary:
      "A dynamic 0-100 composite risk rating synthesizing anomaly confidence and asset tiering.",
    whatIsHere: [
      "Real-time composite score calculated across 30-minute sliding temporal windows",
      "Color-coded operational threat posture (Nominal / Elevated / Critical Alert)",
    ],
    howToUse: [
      "Used by Station Commanders to declare containment and escalation states.",
      "Scores above 75 trigger emergency analyst triage and SIEM alert dispatch.",
    ],
  },
  {
    route: "/monitor",
    targetId: "tour-live-filters",
    locationLabel: "LIVE MONITOR // FILTER & SEARCH BAR",
    title: "5. Telemetry Filter & Forensic Search Bar",
    summary:
      "Real-time filtering controls to isolate specific attack types and network entities.",
    whatIsHere: [
      "Threat Class Filter (DDoS, C2 Beaconing, Recon, DGA / Tunnel, TLS, Exfiltration)",
      "Severity Filter (Critical, High, Medium, Low)",
      "Sub-second Search Bar matching source IP, destination IP, flow IDs, and hashes",
    ],
    howToUse: [
      "Select 'CRITICAL' in the severity dropdown to instantly filter out background noise.",
      "Type any internal host IP into the search box to track all sessions involving that host.",
    ],
  },
  {
    route: "/monitor",
    targetId: "tour-live-table",
    locationLabel: "LIVE MONITOR // TELEMETRY FEED",
    title: "6. Zero-Refresh Live Telemetry Feed",
    summary:
      "Real-time streaming table powered by authenticated WebSocket telemetry directly from the data diode.",
    whatIsHere: [
      "Live stream of classified alerts with MITRE ATT&CK tactic tags",
      "Source/Destination host IPs, protocol, byte volumes, and composite risk score",
      "One-click 'EVIDENCE →' inspection link for every alert",
    ],
    howToUse: [
      "Observe incoming flows as they stream without page reloads.",
      "Click 'EVIDENCE →' on any row to open the Explainable AI evidence explorer for that alert.",
    ],
  },
  {
    route: "/incidents/INC-2026-0831-01",
    targetId: "tour-incident-timeline",
    locationLabel: "INCIDENT DOSSIER // TEMPORAL GRAPH",
    title: "7. Incident Dossier & Kill-Chain Progression",
    summary:
      "Chronological multi-stage attack chains synthesized across 30-minute rolling graph windows.",
    whatIsHere: [
      "Multi-stage timeline (e.g. Reconnaissance → C2 Beaconing → Exfiltration Spike)",
      "Exact timestamps, communicating IPs, and MITRE technique tags for each stage",
      "Correlation Inference Engine reasoning explaining why disparate alerts were unified",
    ],
    howToUse: [
      "Follow the numbered stages from top to bottom to trace the attacker's progression.",
      "Click 'VIEW INCIDENT IN NEO4J GRAPH CANVAS' to pivot into the interactive 3D topology.",
    ],
  },
  {
    route: "/alerts/ALT-001/evidence",
    targetId: "tour-evidence-meters",
    locationLabel: "EVIDENCE EXPLORER // HEURISTIC METERS",
    title: "8. Statistical Evidence & Entropy Meters",
    summary:
      "Raw telemetry and statistical anomaly meters that triggered heuristic detection.",
    whatIsHere: [
      "Shannon Flow Entropy meter (identifies encrypted C2 tunnels and packed payloads)",
      "TCP SYN/ACK ratio meter (detects volumetric SYN floods and port sweeps)",
      "Inter-Arrival Time (IAT) periodicity meter (pinpoints automated C2 beacons)",
    ],
    howToUse: [
      "Compare meter values against nominal baseline thresholds to verify alert validity.",
      "Use these mathematical proofs to justify defensive isolation or firewall rules.",
    ],
  },
  {
    route: "/alerts/ALT-001/evidence",
    targetId: "tour-evidence-shap",
    locationLabel: "EVIDENCE EXPLORER // EXPLAINABLE AI",
    title: "9. TreeSHAP Feature Attributions",
    summary:
      "Complete transparency into machine learning decision boundaries using signed SHAP values.",
    whatIsHere: [
      "Signed SHAP waterfall bars (Red pushes toward threat; Green pushes toward nominal)",
      "Exact feature importance weights for the LightGBM inference model",
      "Composite classification confidence percentage",
    ],
    howToUse: [
      "Inspect the dominant red bars to understand exactly what features triggered the AI.",
      "Eliminates 'black-box' ambiguity during critical security audits and forensics.",
    ],
  },
  {
    route: "/graph",
    targetId: "tour-graph-canvas",
    locationLabel: "NETWORK GRAPH // 3D ORBITAL CANVAS",
    title: "10. 3D Evidence Graph & Node Inspector",
    summary:
      "Interactive 3D graph canvas mapping host nodes and network communication arcs.",
    whatIsHere: [
      "Orbit / Pan / Zoom 3D WebGL camera with real Bloom glow effects",
      "Interactive Host Nodes clickable for live forensic inspection",
      "Right-hand Node Telemetry Inspector showing connected flow arcs and risk ratings",
    ],
    howToUse: [
      "Left-click and drag with your mouse to rotate the perimeter sphere; scroll to zoom.",
      "Click any host sphere to inspect its IP address, risk score, and active attack edges.",
    ],
  },
  {
    route: "/threats",
    targetId: "tour-sonar-chart",
    locationLabel: "THREAT CENTER // D3 RADAR SWEEP",
    title: "11. Threat Center & D3 Radial Sonar Sweep",
    summary:
      "Polar coordinate sonar visualization mapping threat distributions and severity wedges.",
    whatIsHere: [
      "Concentric sonar rings (25%, 50%, 75%, 100%)",
      "Interactive polar wedge arcs sized by alert volume and colored by risk score",
      "Forensic profile drilldown pane and historical time filters (1h, 24h, 7d, 30d)",
    ],
    howToUse: [
      "Click any wedge segment to inspect specific class metrics (e.g. DDoS vs C2 Beaconing).",
      "Toggle time filters in the top right to analyze weekly or monthly baselines.",
    ],
  },
  {
    route: "/replay",
    targetId: "tour-replay-console",
    locationLabel: "REPLAY LAB // ATTACK SIMULATOR",
    title: "12. Replay Lab Scenario Simulator",
    summary:
      "Hardware-isolated simulation console with physical-style toggle switches for live demonstrations.",
    whatIsHere: [
      "Pre-configured scenarios: Multi-Stage APT, DDoS Flood, DGA C2, Exfil Spike",
      "Physical interface safety isolation guard (prevents non-loopback transmission)",
      "Live trigger buttons that inject real synthetic telemetry into the pipeline",
    ],
    howToUse: [
      "Toggle the switch to 'ARMED' on any scenario (e.g. Multi-Stage APT Intrusion).",
      "Click 'ENGAGE' to inject telemetry and watch alerts propagate live across all consoles.",
    ],
  },
  {
    route: "/performance",
    targetId: "tour-perf-charts",
    locationLabel: "PERFORMANCE // SLA TELEMETRY",
    title: "13. SLA Telemetry & Latency Percentiles",
    summary:
      "Sub-second performance monitoring proving the platform's high-throughput capability.",
    whatIsHere: [
      "P99 Pipeline Latency (< 5.0 ms SLA target verification)",
      "Real-time event throughput area charts (benchmarked at 124,850 EPS)",
      "Cluster CPU usage and Kafka consumer group lag (0 ms backpressure)",
    ],
    howToUse: [
      "Verify that P99 latency remains under 5.0 ms during heavy simulated traffic.",
      "Demonstrate platform scalability and zero packet drop to SOC reviewers.",
    ],
  },
  {
    route: "/settings",
    targetId: "tour-settings-panel",
    locationLabel: "STATION SETTINGS // PREFERENCES",
    title: "14. Server-Persisted Settings & Accessibility",
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

  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null);

  const currentStep = INTERACTIVE_TOUR_STEPS[tourStepIndex] || INTERACTIVE_TOUR_STEPS[0];
  const isLast = tourStepIndex === INTERACTIVE_TOUR_STEPS.length - 1;
  const isFirst = tourStepIndex === 0;

  // Auto-navigate to the step's designated route so the user sees the real page
  useEffect(() => {
    if (tourActive && currentStep && location.pathname !== currentStep.route) {
      navigate(currentStep.route);
    }
  }, [tourActive, tourStepIndex, currentStep, location.pathname, navigate]);

  // Compute bounding box of the targeted element to create spotlight cutout
  useEffect(() => {
    if (!tourActive || !currentStep) return;

    const updateRect = () => {
      if (currentStep.targetId) {
        const el = document.getElementById(currentStep.targetId);
        if (el) {
          const rect = el.getBoundingClientRect();
          setHighlightRect(rect);
          // Scroll element into view smoothly if needed
          el.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
          return;
        }
      }
      setHighlightRect(null);
    };

    const timer = setTimeout(updateRect, 300);
    window.addEventListener("resize", updateRect);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", updateRect);
    };
  }, [tourActive, tourStepIndex, currentStep, location.pathname]);

  if (!tourActive) return null;

  return (
    <div className="fixed inset-0 z-50 pointer-events-none select-none font-mono">
      {/* Target Element Spotlight Cutout & Glowing Halo */}
      {highlightRect && (
        <div
          className="fixed pointer-events-none z-40 transition-all duration-500 ease-out rounded-2xl border-2 border-[#3FC7D4] shadow-[0_0_40px_rgba(63,199,212,0.45)]"
          style={{
            top: `${Math.max(0, highlightRect.top - 8)}px`,
            left: `${Math.max(0, highlightRect.left - 8)}px`,
            width: `${highlightRect.width + 16}px`,
            height: `${highlightRect.height + 16}px`,
          }}
        >
          {/* Animated Pulsing Corner Accents */}
          <span className="absolute -top-1.5 -left-1.5 w-3 h-3 border-t-2 border-l-2 border-[#3FC7D4] animate-ping" />
          <span className="absolute -bottom-1.5 -right-1.5 w-3 h-3 border-b-2 border-r-2 border-[#3FC7D4] animate-ping" />
          
          {/* Floating Target Badge */}
          <div className="absolute -top-3 right-4 px-2.5 py-0.5 rounded bg-[#3FC7D4] text-[#0B1220] text-[10px] font-bold tracking-wider uppercase shadow-md flex items-center gap-1">
            <Target className="w-3 h-3" />
            <span>ACTIVE FOCUS TARGET</span>
          </div>
        </div>
      )}

      {/* Ambient Tactical Dark Dimmer */}
      <div className="absolute inset-0 bg-[#0B1220]/75 backdrop-blur-[2px] pointer-events-auto" />

      {/* Floating Comprehensive Tactical Station Guide Panel */}
      <div className="absolute bottom-6 right-6 w-full max-w-xl p-6 rounded-2xl bg-[#131B2E] border-2 border-[#3FC7D4] shadow-[0_0_50px_rgba(63,199,212,0.3)] space-y-4 pointer-events-auto max-h-[90vh] overflow-y-auto z-50">
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
