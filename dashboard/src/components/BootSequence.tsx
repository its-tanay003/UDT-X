import React, { useState, useEffect } from "react";
import { Shield, CheckCircle, Radio, Terminal } from "lucide-react";

interface BootSequenceProps {
  onComplete: () => void;
}

const BOOT_STEPS = [
  "INITIALIZING ENCLAVE INTERFACE...",
  "AUTHENTICATING AIR-GAPPED STATION CREDENTIALS...",
  "ESTABLISHING ONE-WAY TELEMETRY LINK (DATA DIODE)...",
  "HYDRATING DETECTION ENGINES [7/7 ONLINE]...",
  "STATION READY // SIGINT LISTENING POST ACTIVE",
];

export const BootSequence: React.FC<BootSequenceProps> = ({ onComplete }) => {
  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const [activeStep, setActiveStep] = useState(prefersReducedMotion ? BOOT_STEPS.length : 0);

  useEffect(() => {
    if (prefersReducedMotion) {
      const timer = setTimeout(onComplete, 800);
      return () => clearTimeout(timer);
    }

    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev + 1 >= BOOT_STEPS.length) {
          clearInterval(interval);
          setTimeout(onComplete, 700);
          return prev + 1;
        }
        return prev + 1;
      });
    }, 600);

    // Hard fallback timeout (8s)
    const fallbackTimeout = setTimeout(onComplete, 8000);

    return () => {
      clearInterval(interval);
      clearTimeout(fallbackTimeout);
    };
  }, [onComplete, prefersReducedMotion]);

  return (
    <div className="w-screen h-screen bg-[#0B1220] flex flex-col items-center justify-center p-6 relative select-none font-mono">
      {/* Sonar Glow in Background */}
      <div className="absolute w-96 h-96 rounded-full bg-[#3FC7D4]/5 blur-3xl pointer-events-none" />

      <div className="w-full max-w-lg p-8 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/30 shadow-2xl space-y-6 relative z-10">
        <div className="flex items-center gap-3 pb-4 border-b border-[#3FC7D4]/15">
          <div className="w-9 h-9 rounded-lg bg-[#3FC7D4]/20 border border-[#3FC7D4]/50 flex items-center justify-center shadow-[0_0_12px_rgba(63,199,212,0.3)]">
            <Terminal className="w-5 h-5 text-[#3FC7D4]" />
          </div>
          <div>
            <div className="font-bold text-sm tracking-wider text-[#E7ECF5]">
              UDT-X SYSTEM BOOTSTRAP
            </div>
            <div className="text-[10px] text-[#8A95AA]">
              DATA-DIODE PASSIVE SENSOR ENCLAVE
            </div>
          </div>
        </div>

        {/* Terminal Line Output */}
        <div className="space-y-3 min-h-48 text-xs">
          {BOOT_STEPS.map((step, idx) => {
            const isVisible = idx <= activeStep;
            const isFinished = idx < activeStep;
            const isCurrent = idx === activeStep;

            if (!isVisible) return null;

            return (
              <div
                key={idx}
                className={`flex items-center gap-3 transition-opacity duration-300 ${
                  isCurrent ? "text-[#3FC7D4]" : isFinished ? "text-[#4CAF7D]" : "text-[#8A95AA]"
                }`}
              >
                {isFinished ? (
                  <CheckCircle className="w-4 h-4 shrink-0 text-[#4CAF7D]" />
                ) : (
                  <span className="w-4 h-4 rounded-full border border-[#3FC7D4] border-t-transparent animate-spin shrink-0" />
                )}
                <span>{step}</span>
              </div>
            );
          })}
        </div>

        <div className="pt-2 border-t border-[#3FC7D4]/10 flex items-center justify-between text-[10px] text-[#8A95AA]">
          <span>HARDWARE: AIR-GAPPED NODE</span>
          <span className="text-[#3FC7D4]">PASSIVE STREAM (RX ONLY)</span>
        </div>
      </div>
    </div>
  );
};
