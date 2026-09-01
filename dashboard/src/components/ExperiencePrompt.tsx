import React, { useState } from "react";
import {
  Shield,
  Radio,
  Sparkles,
  Zap,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Terminal,
  HelpCircle,
  Activity,
  Layers,
  Cpu,
  Lock,
  Compass,
  Play,
  RotateCcw,
} from "lucide-react";
import { useAuthStore } from "../lib/auth";

interface OnboardingFlowProps {
  onComplete: () => void;
}

interface InteractiveModule {
  id: string;
  badge: string;
  title: string;
  subtitle: string;
  icon: any;
  accentColor: string;
  description: string;
  keyPillars: { icon: any; title: string; desc: string }[];
  interactiveDemoType: "diode" | "engines" | "why" | "roi";
}

const MODULES: InteractiveModule[] = [
  {
    id: "what-is-udtx",
    badge: "MODULE 01 // ARCHITECTURAL FOUNDATION",
    title: "What is UDT-X?",
    subtitle: "Passive One-Way Data-Diode Threat Detection Platform",
    icon: Shield,
    accentColor: "#3FC7D4",
    description:
      "UDT-X (Unified Defense & Telemetry Platform) is a mission-critical cybersecurity system engineered strictly for data-diode-fed, mirrored-traffic, and air-gapped critical infrastructure enclaves where return network paths are physically prohibited.",
    keyPillars: [
      {
        icon: Lock,
        title: "Physically Passive (Zero TX)",
        desc: "Traffic is ingested strictly via unidirectional fiber optical data diodes. The platform has zero attack surface and never injects packets into your monitored network.",
      },
      {
        icon: Activity,
        title: "High-Throughput Telemetry",
        desc: "Engineered in Rust & Python to sustain 124,850+ Events Per Second with sub-5ms P99 latency and zero backpressure.",
      },
      {
        icon: Layers,
        title: "Explainable AI (TreeSHAP)",
        desc: "Every ML anomaly score is accompanied by signed feature attribution waterfalls so operators can explain every trigger to auditors.",
      },
    ],
    interactiveDemoType: "diode",
  },
  {
    id: "how-it-works",
    badge: "MODULE 02 // ENGINE SUBSYSTEMS",
    title: "How Does It Work?",
    subtitle: "7-Stage Detection & Correlation Pipeline",
    icon: Cpu,
    accentColor: "#FF8A3D",
    description:
      "Raw telemetry is ingested from mirrored network taps, normalized in microsecond queues, and evaluated concurrently through 6 specialized heuristic algorithms + 1 LightGBM TreeSHAP model.",
    keyPillars: [
      {
        icon: Radio,
        title: "Heuristic Signature Engines",
        desc: "Volumetric DDoS surge detectors, TCP SYN port scan identifiers, DGA high-entropy domain monitors, and JA3 TLS fingerprint scanners.",
      },
      {
        icon: Sparkles,
        title: "Temporal Graph Correlation",
        desc: "Neo4j graph correlation connects disparate alerts across 30-minute sliding windows into unified multi-stage APT kill-chain dossiers.",
      },
      {
        icon: Zap,
        title: "Composite Risk Scoring",
        desc: "Aggregates heuristic confidence, ML probability, and asset tiering into a real-time 0-100 posture rating.",
      },
    ],
    interactiveDemoType: "engines",
  },
  {
    id: "why-try-udtx",
    badge: "MODULE 03 // DEFENSE ADVANTAGE",
    title: "Why Do You Need UDT-X?",
    subtitle: "Solving Traditional SIEM Fragility in Air-Gapped Environments",
    icon: Zap,
    accentColor: "#FF4757",
    description:
      "Standard cloud SIEMs and active network agents require outbound Internet connectivity, software agents on endpoints, and high operational maintenance. UDT-X eliminates all external dependencies.",
    keyPillars: [
      {
        icon: CheckCircle2,
        title: "No Endpoint Agents Required",
        desc: "Operates 100% at the network perimeter. Zero agents installed on your servers, PLCs, or OT devices.",
      },
      {
        icon: CheckCircle2,
        title: "True Air-Gap Independence",
        desc: "Self-contained heuristic rules, offline ML models, and local databases run entirely on premise without cloud phoning.",
      },
      {
        icon: CheckCircle2,
        title: "Zero Analyst Fatigue",
        desc: "Graph temporal correlation reduces 10,000+ raw flow logs into single actionable incident dossiers.",
      },
    ],
    interactiveDemoType: "why",
  },
  {
    id: "how-it-helps",
    badge: "MODULE 04 // OPERATIONAL IMPACT",
    title: "How Will This Website Help You?",
    subtitle: "Instant Situational Awareness for Defense Operators",
    icon: Compass,
    accentColor: "#4CAF7D",
    description:
      "The UDT-X station console gives your team immediate, real-time command over your monitored enclave through 8 tactical operational screens.",
    keyPillars: [
      {
        icon: Activity,
        title: "3D Ambient Listening Sphere",
        desc: "Visualize inward traffic flow and threat hot-spots instantaneously in real-time WebGL space.",
      },
      {
        icon: Terminal,
        title: "Isolated Replay Lab",
        desc: "Simulate multi-stage APT kill-chains safely to validate defensive readiness and test SOC response procedures.",
      },
      {
        icon: Shield,
        title: "Zero-Latency Live Feed",
        desc: "WebSocket-driven telemetry streaming table allows sub-second threat isolation with instant MITRE ATT&CK mapping.",
      },
    ],
    interactiveDemoType: "roi",
  },
];

export const ExperiencePrompt: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [viewState, setViewState] = useState<"ASK_EXPERIENCE" | "EXPLORE_MODULES">("ASK_EXPERIENCE");
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [activeInteractiveTab, setActiveInteractiveTab] = useState<string>("sim");
  const [simPulseCount, setSimPulseCount] = useState(3);
  const [activeEngineDemo, setActiveEngineDemo] = useState<string>("ddos");
  const { startTour } = useAuthStore();

  const handleUserExperienced = () => {
    // User already knows UDT-X -> Go straight to dashboard
    onComplete();
  };

  const handleUserNew = () => {
    // User is new -> Open step-by-step interactive onboarding briefing
    setViewState("EXPLORE_MODULES");
  };

  const handleFinishBriefing = (launchTour: boolean) => {
    if (launchTour) {
      startTour();
    }
    onComplete();
  };

  const currentModule = MODULES[currentModuleIndex];
  const isLast = currentModuleIndex === MODULES.length - 1;
  const isFirst = currentModuleIndex === 0;

  // View 1: Initial Question Modal ("Have you used UDT-X before?")
  if (viewState === "ASK_EXPERIENCE") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0B1220] bg-radial from-[#131B2E]/90 to-[#0B1220] font-mono select-none">
        {/* Ambient Glow */}
        <div className="absolute w-[500px] h-[500px] bg-[#3FC7D4]/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="relative w-full max-w-xl p-8 rounded-2xl bg-[#131B2E] border-2 border-[#3FC7D4]/40 shadow-[0_0_60px_rgba(63,199,212,0.25)] space-y-6 text-center animate-fade-in">
          {/* Header Icon */}
          <div className="w-16 h-16 mx-auto rounded-2xl bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center shadow-[0_0_25px_rgba(63,199,212,0.3)]">
            <Shield className="w-8 h-8 text-[#3FC7D4]" />
          </div>

          <div className="space-y-2">
            <div className="text-[11px] font-bold tracking-widest text-[#3FC7D4] uppercase">
              STATION OPERATOR VERIFICATION // ENCLAVE POSTURE
            </div>
            <h1 className="font-display text-2xl font-bold text-[#E7ECF5] tracking-tight">
              Have you operated UDT-X before?
            </h1>
            <p className="text-xs text-[#8A95AA] max-w-md mx-auto leading-relaxed">
              Welcome to the <strong className="text-[#3FC7D4]">UDT-X Passive Defense Station</strong>. Please declare your experience level to customize your terminal initialization.
            </p>
          </div>

          {/* Interactive Option Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 text-left">
            {/* Option A: Yes, I am experienced */}
            <button
              onClick={handleUserExperienced}
              className="p-5 rounded-xl bg-[#0B1220] border border-[#3FC7D4]/20 hover:border-[#4CAF7D] hover:bg-[#1B2540] transition-all group relative overflow-hidden"
            >
              <div className="flex items-center justify-between mb-3">
                <CheckCircle2 className="w-5 h-5 text-[#4CAF7D] group-hover:scale-110 transition-transform" />
                <span className="text-[10px] text-[#4CAF7D] font-bold uppercase tracking-wider">
                  DIRECT ACCESS
                </span>
              </div>
              <h3 className="font-display text-sm font-bold text-[#E7ECF5] group-hover:text-[#4CAF7D] transition-colors">
                Yes, I have used it
              </h3>
              <p className="text-[11px] text-[#8A95AA] mt-1 leading-relaxed">
                Skip system briefing and initialize directly into the live Security Command Center.
              </p>
            </button>

            {/* Option B: No, I am new */}
            <button
              onClick={handleUserNew}
              className="p-5 rounded-xl bg-[#0B1220] border-2 border-[#3FC7D4]/50 hover:border-[#3FC7D4] hover:bg-[#1B2540] transition-all group relative overflow-hidden shadow-[0_0_20px_rgba(63,199,212,0.15)]"
            >
              <div className="flex items-center justify-between mb-3">
                <Sparkles className="w-5 h-5 text-[#3FC7D4] animate-pulse group-hover:scale-110 transition-transform" />
                <span className="text-[10px] text-[#3FC7D4] font-bold uppercase tracking-wider">
                  RECOMMENDED
                </span>
              </div>
              <h3 className="font-display text-sm font-bold text-[#E7ECF5] group-hover:text-[#3FC7D4] transition-colors">
                No, I am new here
              </h3>
              <p className="text-[11px] text-[#8A95AA] mt-1 leading-relaxed">
                Step-by-step interactive orientation: What it is, how it works, why you need it, and how it helps.
              </p>
            </button>
          </div>

          {/* Footer Subtext */}
          <div className="pt-2 text-[10px] text-[#8A95AA] flex items-center justify-center gap-2">
            <Lock className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>ENCLAVE SECURITY CLEARANCE: LEVEL-4 OPERATOR</span>
          </div>
        </div>
      </div>
    );
  }

  // View 2: Step-by-Step Interactive Animated Briefing (What, How, Why, ROI)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-[#0B1220]/95 backdrop-blur-md font-mono select-none overflow-y-auto">
      {/* Background Animated Halo */}
      <div
        className="absolute w-[600px] h-[600px] rounded-full blur-[140px] pointer-events-none transition-colors duration-700"
        style={{ backgroundColor: `${currentModule.accentColor}15` }}
      />

      <div className="relative w-full max-w-4xl p-6 md:p-8 rounded-3xl bg-[#131B2E] border-2 shadow-[0_0_80px_rgba(0,0,0,0.8)] space-y-6 transition-all duration-500 my-auto"
        style={{ borderColor: `${currentModule.accentColor}60` }}
      >
        {/* Top Progress Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#3FC7D4]/15">
          <div className="flex items-center gap-2">
            <div
              className="p-2 rounded-xl flex items-center justify-center shadow-md"
              style={{
                backgroundColor: `${currentModule.accentColor}20`,
                borderColor: `${currentModule.accentColor}50`,
                borderWidth: "1px",
                color: currentModule.accentColor,
              }}
            >
              <currentModule.icon className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div
                className="text-[10px] font-bold uppercase tracking-widest"
                style={{ color: currentModule.accentColor }}
              >
                {currentModule.badge}
              </div>
              <div className="text-xs text-[#8A95AA]">
                STAGE {currentModuleIndex + 1} OF {MODULES.length}
              </div>
            </div>
          </div>

          {/* Module Step Indicators */}
          <div className="flex items-center gap-2">
            {MODULES.map((m, idx) => (
              <button
                key={m.id}
                onClick={() => setCurrentModuleIndex(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === currentModuleIndex
                    ? "w-8 bg-[#3FC7D4]"
                    : idx < currentModuleIndex
                    ? "w-3 bg-[#4CAF7D]"
                    : "w-3 bg-[#1B2540]"
                }`}
                title={m.title}
              />
            ))}
          </div>

          <button
            onClick={() => handleFinishBriefing(false)}
            className="text-xs text-[#8A95AA] hover:text-[#E7ECF5] hover:underline"
          >
            SKIP ORIENTATION ✕
          </button>
        </div>

        {/* Module Title & Hero Description */}
        <div className="space-y-2">
          <h2 className="font-display text-2xl md:text-3xl font-bold text-[#E7ECF5] tracking-tight flex items-center gap-3">
            <span>{currentModule.title}</span>
          </h2>
          <div className="text-xs md:text-sm font-semibold" style={{ color: currentModule.accentColor }}>
            {currentModule.subtitle}
          </div>
          <p className="text-xs md:text-sm text-[#8A95AA] leading-relaxed max-w-3xl pt-1">
            {currentModule.description}
          </p>
        </div>

        {/* Main Body: 3 Structured Pillars + Interactive Micro-Lab */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
          {/* Left Column: 3 Pillars */}
          <div className="lg:col-span-6 space-y-3">
            <div className="text-[11px] font-bold text-[#E7ECF5] uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5" style={{ color: currentModule.accentColor }} />
              <span>CORE ARCHITECTURAL PILLARS</span>
            </div>

            {currentModule.keyPillars.map((p, idx) => {
              const PillarIcon = p.icon;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-[#0B1220] border border-[#3FC7D4]/15 hover:border-[#3FC7D4]/40 transition-all space-y-1.5"
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className="p-1.5 rounded-lg"
                      style={{
                        backgroundColor: `${currentModule.accentColor}15`,
                        color: currentModule.accentColor,
                      }}
                    >
                      <PillarIcon className="w-4 h-4" />
                    </div>
                    <h4 className="text-xs font-bold text-[#E7ECF5]">{p.title}</h4>
                  </div>
                  <p className="text-[11px] text-[#8A95AA] leading-relaxed pl-8">
                    {p.desc}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Right Column: Interactive Micro-Lab Animation */}
          <div className="lg:col-span-6 rounded-2xl bg-[#0B1220] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#3FC7D4]/10">
              <span className="text-[10px] text-[#8A95AA] uppercase font-bold flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-[#3FC7D4]" />
                LIVE INTERACTIVE SIMULATOR
              </span>
              <span className="text-[10px] text-[#4CAF7D] font-bold animate-pulse">
                ● ACTIVE LAB
              </span>
            </div>

            {/* Interactive Module 1: Data Diode Simulator */}
            {currentModule.interactiveDemoType === "diode" && (
              <div className="space-y-4 my-auto py-2">
                <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-center">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#8A95AA]">MONITORED TAP (TX)</span>
                    <span className="text-[#3FC7D4] font-bold">PHYSICAL DATA DIODE</span>
                    <span className="text-[#4CAF7D]">UDT-X ENCLAVE (RX)</span>
                  </div>

                  {/* Flow Animation Graphic */}
                  <div className="relative h-12 bg-[#0B1220] rounded-lg border border-[#3FC7D4]/15 flex items-center justify-between px-4 overflow-hidden">
                    <div className="w-3 h-3 rounded-full bg-[#3FC7D4] animate-ping" />
                    
                    {/* Directional Inward Particle Track */}
                    <div className="flex-1 flex items-center justify-center gap-2 text-[10px] text-[#3FC7D4] font-bold">
                      <span className="animate-pulse">━━━━━━▶</span>
                      <span className="px-2 py-0.5 rounded bg-[#3FC7D4]/20 border border-[#3FC7D4]/40">
                        ONE-WAY OPTICAL FIBER
                      </span>
                      <span className="animate-pulse">━━━━━━▶</span>
                    </div>

                    <div className="w-3 h-3 rounded-full bg-[#4CAF7D]" />
                  </div>

                  <div className="text-[10px] text-[#8A95AA]">
                    Click below to transmit a simulated network packet through the physical diode:
                  </div>

                  <button
                    onClick={() => setSimPulseCount((p) => p + 1)}
                    className="w-full py-2 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold text-xs hover:bg-[#35B2BE] transition-all flex items-center justify-center gap-2"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    TRANSMIT PACKET PULSE ({simPulseCount} INGESTED)
                  </button>
                </div>
              </div>
            )}

            {/* Interactive Module 2: Detection Engine Demo */}
            {currentModule.interactiveDemoType === "engines" && (
              <div className="space-y-3 my-auto">
                <div className="text-[11px] text-[#8A95AA]">
                  Select an engine to inspect its real-time heuristic logic:
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { id: "ddos", label: "5a DDoS Surge", metric: "15,200 pkts/s" },
                    { id: "c2", label: "5c C2 Beacon", metric: "60.0s IAT Jitter" },
                    { id: "dga", label: "5d DGA Tunnel", metric: "4.65 Entropy" },
                    { id: "shap", label: "ML TreeSHAP", metric: "LightGBM +0.38" },
                  ].map((eng) => (
                    <button
                      key={eng.id}
                      onClick={() => setActiveEngineDemo(eng.id)}
                      className={`p-2.5 rounded-lg border text-left transition-all ${
                        activeEngineDemo === eng.id
                          ? "bg-[#1B2540] border-[#FF8A3D] text-[#FF8A3D] font-bold"
                          : "bg-[#131B2E] border-[#3FC7D4]/15 text-[#8A95AA] hover:text-[#E7ECF5]"
                      }`}
                    >
                      <div className="text-[10px]">{eng.label}</div>
                      <div className="text-[11px] text-[#E7ECF5] font-bold">{eng.metric}</div>
                    </button>
                  ))}
                </div>

                <div className="p-3 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/15 text-[11px] text-[#8A95AA] space-y-1">
                  <span className="text-[#FF8A3D] font-bold uppercase">Classification Rule:</span>
                  <p>
                    {activeEngineDemo === "ddos" && "Flags volumetric packet surges with > 0.95 SYN/ACK ratio asymmetry."}
                    {activeEngineDemo === "c2" && "Calculates Fourier transform on Inter-Arrival Times to spot programmatic periodic beacons."}
                    {activeEngineDemo === "dga" && "Calculates Shannon character entropy on DNS queries to detect algorithmic domain fluxing."}
                    {activeEngineDemo === "shap" && "Computes signed local game-theoretic feature contributions for explainable machine learning."}
                  </p>
                </div>
              </div>
            )}

            {/* Interactive Module 3: Why UDT-X Comparison Table */}
            {currentModule.interactiveDemoType === "why" && (
              <div className="space-y-3 my-auto font-mono text-xs">
                <div className="p-3.5 rounded-xl bg-[#131B2E] border border-[#FF4757]/30 space-y-2">
                  <div className="flex justify-between text-[11px] font-bold text-[#FF4757]">
                    <span>TRADITIONAL SIEM</span>
                    <span>UDT-X DATA DIODE</span>
                  </div>
                  <div className="space-y-1.5 text-[10px] text-[#8A95AA]">
                    <div className="flex justify-between py-1 border-b border-[#3FC7D4]/10">
                      <span>Requires internet cloud sync</span>
                      <span className="text-[#4CAF7D] font-bold">100% Air-Gapped Offline</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#3FC7D4]/10">
                      <span>Heavy endpoint agents</span>
                      <span className="text-[#4CAF7D] font-bold">Zero Endpoint Footprint</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span>Black-box AI alert flood</span>
                      <span className="text-[#4CAF7D] font-bold">TreeSHAP Explainable</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Interactive Module 4: Live Station Capabilities ROI */}
            {currentModule.interactiveDemoType === "roi" && (
              <div className="space-y-3 my-auto">
                <div className="p-4 rounded-xl bg-[#131B2E] border border-[#4CAF7D]/30 text-center space-y-2">
                  <Compass className="w-8 h-8 text-[#4CAF7D] mx-auto animate-spin" />
                  <h4 className="text-sm font-bold text-[#E7ECF5]">
                    8 Unified Analyst Consoles
                  </h4>
                  <p className="text-[11px] text-[#8A95AA]">
                    Overview, Live Monitor, Incident Dossiers, Evidence XAI, 3D Graph, Threat Sonar, Replay Lab, and SLA Performance.
                  </p>
                </div>
              </div>
            )}

            {/* Station Status Bottom Tag */}
            <div className="text-[10px] text-[#8A95AA] flex items-center justify-between pt-2 border-t border-[#3FC7D4]/10">
              <span>HARDWARE POSTURE: AIR-GAPPED</span>
              <span className="text-[#3FC7D4]">ENCLAVE v1.0.0</span>
            </div>
          </div>
        </div>

        {/* Navigation & Action Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-[#3FC7D4]/15 text-xs">
          <div>
            {!isFirst && (
              <button
                onClick={() => setCurrentModuleIndex((i) => i - 1)}
                className="px-4 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] flex items-center gap-1.5 transition-colors font-bold"
              >
                <ArrowLeft className="w-4 h-4" />
                PREVIOUS MODULE
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {isLast ? (
              <>
                <button
                  onClick={() => handleFinishBriefing(true)}
                  className="px-5 py-2.5 rounded-xl bg-[#0B1220] border border-[#3FC7D4] text-[#3FC7D4] font-bold hover:bg-[#3FC7D4]/15 transition-all flex items-center gap-2"
                >
                  <Compass className="w-4 h-4" />
                  START INTERACTIVE TOUR
                </button>
                <button
                  onClick={() => handleFinishBriefing(false)}
                  className="px-6 py-2.5 rounded-xl bg-[#4CAF7D] text-[#0B1220] font-bold hover:bg-[#43A047] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(76,175,125,0.4)]"
                >
                  <span>ENTER COMMAND CENTER</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </>
            ) : (
              <button
                onClick={() => setCurrentModuleIndex((i) => i + 1)}
                className="px-6 py-2.5 rounded-xl bg-[#3FC7D4] text-[#0B1220] font-bold hover:bg-[#35B2BE] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(63,199,212,0.3)]"
              >
                <span>NEXT: {MODULES[currentModuleIndex + 1].title}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
