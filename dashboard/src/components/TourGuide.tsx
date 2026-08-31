import React from "react";
import { Compass, ArrowRight, ArrowLeft, X, Shield } from "lucide-react";
import { useAuthStore } from "../lib/auth";

interface TourStep {
  title: string;
  briefing: string;
  targetHint: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    title: "TACTICAL CONSOLE RAIL",
    briefing:
      "Your persistent mission-control sidebar. Track the live hardware status of the inward data diode and switch instantaneously between the 8 primary analyst consoles.",
    targetHint: "Left Sidebar // Navigation",
  },
  {
    title: "AMBIENT LISTENING SPHERE",
    briefing:
      "Physical rendering of the data diode thesis. Particles travel strictly inward along real network communication arcs, dynamically colored by threat severity.",
    targetHint: "Overview Screen // 3D Perimeter",
  },
  {
    title: "KEY PERFORMANCE INSTRUMENTS",
    briefing:
      "Real-time wire ingestion rate (124,850 EPS benchmark), active anomalous sessions, kill-chain incidents, and MITRE-scored alert frequencies.",
    targetHint: "Top Metrics // KPI Grid",
  },
  {
    title: "LIVE TELEMETRY MONITOR",
    briefing:
      "Zero-refresh streaming feed of incoming network flows and classified alerts. Filter by threat class, severity level, or search by host IP.",
    targetHint: "Live Monitor Console",
  },
  {
    title: "INCIDENT DOSSIER & KILL-CHAINS",
    briefing:
      "Multi-stage temporal graph correlations mapped across 30-minute sliding windows. Inspect chronological attack stages and correlation reasoning.",
    targetHint: "Incident Dossier",
  },
  {
    title: "EVIDENCE EXPLORER & TREESHAP",
    briefing:
      "Full explainability for machine learning predictions. View signed TreeSHAP feature attribution waterfalls and raw mathematical entropy meters.",
    targetHint: "Evidence Explorer",
  },
  {
    title: "REPLAY LAB ATTACK SIMULATOR",
    briefing:
      "Hardware-isolated scenario runner to simulate multi-stage APT kill-chains, DDoS surges, DGA fluxing, and DNS tunnels for defensive benchmarking.",
    targetHint: "Replay Lab",
  },
  {
    title: "STATION CONFIGURATION & PREFERENCES",
    briefing:
      "Persist notification thresholds, 3D sphere density modes, audio alerts, and SIEM export defaults server-side to your analyst account.",
    targetHint: "Settings Console",
  },
];

export const TourGuide: React.FC = () => {
  const {
    tourActive,
    tourStepIndex,
    nextTourStep,
    prevTourStep,
    skipTour,
    completeTour,
  } = useAuthStore();

  if (!tourActive) return null;

  const currentStep = TOUR_STEPS[tourStepIndex] || TOUR_STEPS[0];
  const isLast = tourStepIndex === TOUR_STEPS.length - 1;
  const isFirst = tourStepIndex === 0;

  return (
    <div className="fixed inset-0 z-50 pointer-events-none select-none">
      {/* Dimmed Focus Backdrop */}
      <div className="absolute inset-0 bg-[#0B1220]/65 backdrop-blur-[2px] pointer-events-auto" />

      {/* Floating Tactical Briefing Card */}
      <div className="absolute bottom-8 right-8 w-full max-w-md p-6 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/40 shadow-2xl space-y-4 pointer-events-auto font-mono">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#3FC7D4]/15">
          <div className="flex items-center gap-2 text-xs font-bold text-[#3FC7D4]">
            <Compass className="w-4 h-4 animate-spin" />
            <span>STATION BRIEFING // STEP {String(tourStepIndex + 1).padStart(2, "0")} / {String(TOUR_STEPS.length).padStart(2, "0")}</span>
          </div>
          <button
            onClick={skipTour}
            className="p-1 rounded text-[#8A95AA] hover:text-[#E7ECF5] hover:bg-[#0B1220]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-2">
          <div className="text-[10px] text-[#3FC7D4] uppercase tracking-wider">
            FOCUS: {currentStep.targetHint}
          </div>
          <h3 className="font-display text-base font-bold text-[#E7ECF5]">
            {currentStep.title}
          </h3>
          <p className="text-xs text-[#8A95AA] leading-relaxed">
            {currentStep.briefing}
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between pt-3 border-t border-[#3FC7D4]/10 text-xs">
          <button
            onClick={skipTour}
            className="text-[11px] text-[#8A95AA] hover:text-[#E7ECF5] hover:underline"
          >
            DISMISS TOUR
          </button>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                onClick={prevTourStep}
                className="px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                PREV
              </button>
            )}

            <button
              onClick={isLast ? completeTour : nextTourStep}
              className="px-4 py-1.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold hover:bg-[#35B2BE] transition-all flex items-center gap-1.5"
            >
              <span>{isLast ? "COMPLETE BRIEFING" : "NEXT"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
