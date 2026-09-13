import React from "react";
import { Link } from "react-router-dom";
import { Shield, Radio, Flame, Cpu, Terminal, ArrowRight, Lock, Zap, CheckCircle2, Globe, Activity } from "lucide-react";
import { useAuthStore } from "../lib/auth";
import { SEO } from "../components/SEO";

export const LandingPage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220] flex flex-col">
      <SEO
        title="UDT-X — Unified Dynamic Threat Identification & Autonomous Defense Platform"
        description="Autonomous SIGINT Enclave with physical unidirectional data diode tap, 7-engine real-time threat correlation, TreeSHAP explainable AI, and sub-5ms SLA."
        canonical="https://udtx.security/"
      />

      {/* Header Bar */}
      <header className="w-full border-b border-[#3FC7D4]/15 bg-[#0B1220]/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-8 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-[#3FC7D4] rounded-lg p-1">
          <div className="w-9 h-9 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center transition-transform group-hover:scale-105 shadow-[0_0_15px_rgba(63,199,212,0.2)]">
            <Shield className="w-5 h-5 text-[#3FC7D4]" />
          </div>
          <div>
            <div className="font-display font-bold text-sm tracking-wider text-[#E7ECF5]">UDT-X ENCLAVE</div>
            <div className="text-[10px] font-mono text-[#8A95AA]">AUTONOMOUS SIGINT DEFENSE</div>
          </div>
        </Link>

        <nav className="flex items-center gap-6">
          <Link to="/faq" className="text-xs font-mono text-[#8A95AA] hover:text-[#3FC7D4] transition-colors hidden sm:inline-block">
            Architecture FAQ
          </Link>
          <Link to="/privacy" className="text-xs font-mono text-[#8A95AA] hover:text-[#3FC7D4] transition-colors hidden sm:inline-block">
            Privacy (DPDP)
          </Link>
          {user ? (
            <Link
              to="/app"
              className="px-4 py-2 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#35B2BE] transition-all shadow-[0_0_15px_rgba(63,199,212,0.3)] flex items-center gap-1.5"
            >
              <span>Enter Enclave</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <Link
              to="/login"
              className="px-4 py-2 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#35B2BE] transition-all shadow-[0_0_15px_rgba(63,199,212,0.3)] flex items-center gap-1.5"
            >
              <span>Station Login</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 sm:pt-24 pb-20 px-4 sm:px-8 border-b border-[#3FC7D4]/15">
        {/* Glow & Grid backdrop */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(63,199,212,0.1)_0%,transparent_70%)] pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#131B2E15_1px,transparent_1px),linear-gradient(to_bottom,#131B2E15_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

        <div className="max-w-5xl mx-auto text-center space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#131B2E] border border-[#3FC7D4]/30 font-mono text-xs text-[#3FC7D4] shadow-[0_0_15px_rgba(63,199,212,0.15)]">
            <span className="w-2 h-2 rounded-full bg-[#4CAF7D] animate-pulse" />
            <span>AIR-GAPPED DATA DIODE ENCLAVE — v1.5.0 OPERATIONAL</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-display font-extrabold tracking-tight text-[#E7ECF5] leading-tight sm:leading-none">
            Zero-Transmit Network Defense & <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#3FC7D4] to-[#4CAF7D]">Real-Time Threat Correlation</span>
          </h1>

          <p className="max-w-3xl mx-auto text-sm sm:text-base text-[#8A95AA] font-mono leading-relaxed">
            Passive optical listening post ingesting multi-gigabit flow telemetry. Sub-millisecond EWMA Gaussian baseline scoring, TreeSHAP explainable AI, and 30-minute rolling graph correlation without sending a single packet back onto the monitored wire.
          </p>

          {/* Primary Clear CTA */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link
                to="/app"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-mono font-bold text-sm uppercase tracking-wider transition-all shadow-[0_0_25px_rgba(63,199,212,0.4)] flex items-center justify-center gap-2"
              >
                <span>Enter Enclave Console</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <Link
                to="/login"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-mono font-bold text-sm uppercase tracking-wider transition-all shadow-[0_0_25px_rgba(63,199,212,0.4)] flex items-center justify-center gap-2"
              >
                <span>Initialize Station Access</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            )}
            <Link
              to="/faq"
              className="w-full sm:w-auto px-6 py-4 rounded-xl bg-[#131B2E] hover:bg-[#1B2540] border border-[#3FC7D4]/30 text-[#E7ECF5] font-mono text-sm transition-colors flex items-center justify-center gap-2"
            >
              <span>Read Architecture FAQ</span>
            </Link>
          </div>

          {/* Key Metrics Strip */}
          <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
              <div className="text-2xl font-display font-bold text-[#3FC7D4]">0.00 ms</div>
              <div className="text-[11px] font-mono text-[#8A95AA]">Inline Network Latency</div>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
              <div className="text-2xl font-display font-bold text-[#4CAF7D]">7 Engines</div>
              <div className="text-[11px] font-mono text-[#8A95AA]">Rule & ML Detection Tier</div>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
              <div className="text-2xl font-display font-bold text-[#FF8A3D]">TreeSHAP</div>
              <div className="text-[11px] font-mono text-[#8A95AA]">Explainable AI Attribution</div>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20">
              <div className="text-2xl font-display font-bold text-[#E7ECF5]">100% DPDP</div>
              <div className="text-[11px] font-mono text-[#8A95AA]">Act 2023 Statutory Privacy</div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillar Grid */}
      <section className="py-16 sm:py-20 px-4 sm:px-8 max-w-6xl mx-auto w-full space-y-12">
        <div className="text-center space-y-2">
          <div className="text-xs font-mono text-[#3FC7D4] uppercase tracking-wider">
            ENCLAVE CAPABILITY STACK
          </div>
          <h2 className="text-2xl sm:text-3xl font-display font-bold text-[#E7ECF5]">
            Hardware-Enforced Security Architecture
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4 hover:border-[#3FC7D4]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4]">
              <Radio className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-display font-bold text-[#E7ECF5]">
              Unidirectional Optical Tap
            </h3>
            <p className="text-xs font-mono text-[#8A95AA] leading-relaxed">
              Physical fiber-optic diode guarantees strictly inward packet flow. Eliminates return-path payload execution, ensuring zero interference with production SCADA and enterprise enclaves.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4 hover:border-[#3FC7D4]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#FF8A3D]/15 border border-[#FF8A3D]/40 flex items-center justify-center text-[#FF8A3D]">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-display font-bold text-[#E7ECF5]">
              7-Engine Anomaly Detection
            </h3>
            <p className="text-xs font-mono text-[#8A95AA] leading-relaxed">
              Dedicated parallel engines for SYN floods, port scan reconnaissance, C2 IAT periodicity jitter, DGA DNS tunneling entropy, TLS encrypted sessions, and data exfiltration.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4 hover:border-[#3FC7D4]/50 transition-all">
            <div className="w-10 h-10 rounded-xl bg-[#4CAF7D]/15 border border-[#4CAF7D]/40 flex items-center justify-center text-[#4CAF7D]">
              <Globe className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-display font-bold text-[#E7ECF5]">
              3D Temporal Graph Kill Chains
            </h3>
            <p className="text-xs font-mono text-[#8A95AA] leading-relaxed">
              Correlates multi-stage cyber attacks across 30-minute rolling Neo4j graph windows with 100% MITRE ATT&CK technique mapping and ArcSight CEF/Syslog export.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#3FC7D4]/15 bg-[#0B1220] py-8 px-4 text-center font-mono text-xs text-[#8A95AA] space-y-3 mt-auto">
        <div className="flex flex-wrap justify-center gap-6">
          <Link to="/faq" className="hover:text-[#3FC7D4] transition-colors">Architecture FAQ</Link>
          <Link to="/privacy" className="hover:text-[#3FC7D4] transition-colors">Privacy Policy (DPDP)</Link>
          <Link to={user ? "/app" : "/login"} className="hover:text-[#3FC7D4] transition-colors">
            {user ? "Enclave Console" : "Station Login"}
          </Link>
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("open-cookie-preferences"))}
            className="hover:text-[#3FC7D4] transition-colors underline"
          >
            Cookie Preferences
          </button>
        </div>
        <div>© 2026 UDT-X Enclave. Apache License 2.0. Compliant with DPDP Act 2023.</div>
      </footer>
    </div>
  );
};
