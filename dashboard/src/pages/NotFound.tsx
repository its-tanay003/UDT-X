import React from "react";
import { Link } from "react-router-dom";
import { AlertOctagon, Radio, ArrowLeft, Shield, Terminal } from "lucide-react";
import { useAuthStore } from "../lib/auth";
import { SEO } from "../components/SEO";

export const NotFoundPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220] flex flex-col items-center justify-center p-4 sm:p-6 relative select-none">
      <SEO
        title="404 — SIGNAL LOST | UDT-X Enclave"
        description="The requested telemetry route or mission console coordinate does not exist in the station registry."
        noIndex={true}
      />

      {/* Grid & Pulse background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,71,87,0.08)_0%,transparent_70%)] pointer-events-none" />

      <div className="max-w-md w-full p-8 rounded-2xl bg-[#131B2E] border border-[#FF4757]/40 shadow-2xl text-center space-y-6 relative z-10">
        {/* Signal Lost Icon */}
        <div className="w-16 h-16 rounded-2xl bg-[#FF4757]/15 border border-[#FF4757]/40 flex items-center justify-center mx-auto text-[#FF4757] shadow-[0_0_25px_rgba(255,71,87,0.3)] animate-pulse">
          <AlertOctagon className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <div className="text-xs font-mono tracking-widest text-[#FF4757] uppercase">
            STATUS 404 // UNKNOWN COORDINATES
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-[#E7ECF5] tracking-tight">
            OPTICAL SIGNAL LOST
          </h1>
          <p className="text-xs font-mono text-[#8A95AA] leading-relaxed">
            The requested telemetry endpoint, route, or forensic artifact cannot be resolved within the UDT-X capability registry.
          </p>
        </div>

        {/* Diagnostic Block */}
        <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-[11px] text-left space-y-1">
          <div className="flex justify-between text-[#8A95AA]">
            <span>DATA DIODE:</span>
            <span className="text-[#4CAF7D]">INWARD PASSIVE</span>
          </div>
          <div className="flex justify-between text-[#8A95AA]">
            <span>OPERATOR STATE:</span>
            <span className={user ? "text-[#3FC7D4]" : "text-[#FF8A3D]"}>
              {user ? `AUTHENTICATED (${user.role.toUpperCase()})` : "UNAUTHENTICATED"}
            </span>
          </div>
        </div>

        {/* Action Link based on auth status */}
        <div className="pt-2">
          {user ? (
            <Link
              to="/app"
              className="w-full py-3 rounded-xl bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(63,199,212,0.3)] flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              <span>Return to Command Center</span>
            </Link>
          ) : (
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/"
                className="flex-1 py-2.5 rounded-xl bg-[#0B1220] border border-[#3FC7D4]/30 hover:bg-[#1B2540] text-[#E7ECF5] font-mono text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Public Home</span>
              </Link>
              <Link
                to="/login"
                className="flex-1 py-2.5 rounded-xl bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(63,199,212,0.3)] flex items-center justify-center gap-1.5"
              >
                <Shield className="w-4 h-4" />
                <span>Station Login</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
