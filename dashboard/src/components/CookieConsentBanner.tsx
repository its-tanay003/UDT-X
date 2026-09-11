import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Shield, Check, X, ChevronRight, Lock } from "lucide-react";
import { getConsentState, setConsentState } from "../lib/analytics";
import type { CookieConsentState } from "../lib/analytics";

export const CookieConsentBanner: React.FC = () => {
  const [showBanner, setShowBanner] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [analyticsOptIn, setAnalyticsOptIn] = useState(false);

  useEffect(() => {
    const existing = getConsentState();
    if (!existing) {
      setShowBanner(true);
    }

    const handleCustomOpen = () => {
      const current = getConsentState();
      setAnalyticsOptIn(current ? current.analytics : false);
      setShowPreferences(true);
      setShowBanner(true);
    };

    window.addEventListener("open-cookie-preferences", handleCustomOpen);
    return () => window.removeEventListener("open-cookie-preferences", handleCustomOpen);
  }, []);

  const handleAcceptAll = () => {
    setConsentState(true);
    setShowBanner(false);
    setShowPreferences(false);
  };

  const handleNecessaryOnly = () => {
    setConsentState(false);
    setShowBanner(false);
    setShowPreferences(false);
  };

  const handleSaveCustom = () => {
    setConsentState(analyticsOptIn);
    setShowBanner(false);
    setShowPreferences(false);
  };

  if (!showBanner) return null;

  return (
    <div
      role="region"
      aria-label="Privacy & Cookie Preferences"
      className="fixed bottom-4 left-4 right-4 md:left-6 md:right-auto md:max-w-xl z-50 p-4 sm:p-5 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/30 shadow-[0_10px_35px_rgba(0,0,0,0.6)] backdrop-blur-md select-none animate-in fade-in slide-in-from-bottom-5 duration-300"
    >
      <div className="space-y-3 font-sans">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center shrink-0 mt-0.5">
            <Shield className="w-4 h-4 text-[#3FC7D4]" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-display font-bold text-sm tracking-wide text-[#E7ECF5]">
                PRIVACY & DATA PROTECTION NOTICE
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0B1220] border border-[#3FC7D4]/20 text-[#3FC7D4]">
                DPDP ACT 2023 COMPLIANT
              </span>
            </div>
            <p className="text-xs text-[#8A95AA] leading-relaxed">
              We collect essential session identifiers strictly necessary for authenticating enclave operations.
              First-party, cookieless metrics help us optimize telemetry processing speed, but require your explicit consent.
              Read our full{" "}
              <Link to="/privacy" className="text-[#3FC7D4] underline hover:text-[#E7ECF5] focus:ring-1 focus:ring-[#3FC7D4]">
                Privacy Policy
              </Link>{" "}
              and{" "}
              <Link to="/terms" className="text-[#3FC7D4] underline hover:text-[#E7ECF5] focus:ring-1 focus:ring-[#3FC7D4]">
                Terms of Use
              </Link>.
            </p>
          </div>
        </div>

        {/* Granular Modal for Preferences */}
        {showPreferences && (
          <div className="p-3 rounded-xl bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2.5 my-2">
            <div className="flex items-center justify-between py-1 border-b border-[#3FC7D4]/10">
              <div className="flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-[#4CAF7D]" />
                <span className="text-xs font-mono font-bold text-[#E7ECF5]">
                  Strictly Necessary (Auth / Session)
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#4CAF7D] bg-[#4CAF7D]/10 px-2 py-0.5 rounded">
                ALWAYS ACTIVE
              </span>
            </div>

            <div className="flex items-center justify-between py-1">
              <div>
                <span className="text-xs font-mono font-bold text-[#E7ECF5] block">
                  Anonymous Performance Telemetry
                </span>
                <span className="text-[10px] text-[#8A95AA]">
                  First-party request latencies and navigation metrics (no personal tracking)
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={analyticsOptIn}
                  onChange={(e) => setAnalyticsOptIn(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-[#131B2E] border border-[#3FC7D4]/30 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-[#0B1220] peer-checked:bg-[#3FC7D4] after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#E7ECF5] after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
              </label>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <button
            onClick={() => setShowPreferences(!showPreferences)}
            className="text-xs font-mono text-[#8A95AA] hover:text-[#3FC7D4] underline flex items-center gap-1 transition-colors"
          >
            {showPreferences ? "Hide Settings" : "Customize Preferences"}
          </button>

          <div className="flex items-center gap-2">
            {showPreferences ? (
              <button
                onClick={handleSaveCustom}
                className="px-3 py-1.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#35B2BE] transition-all shadow-[0_0_10px_rgba(63,199,212,0.2)]"
              >
                Save Preferences
              </button>
            ) : (
              <>
                <button
                  onClick={handleNecessaryOnly}
                  className="px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/30 text-[#E7ECF5] font-mono text-xs hover:bg-[#1B2540] transition-colors"
                >
                  Essential Only
                </button>
                <button
                  onClick={handleAcceptAll}
                  className="px-3.5 py-1.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#35B2BE] transition-all shadow-[0_0_10px_rgba(63,199,212,0.2)]"
                >
                  Accept All
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
