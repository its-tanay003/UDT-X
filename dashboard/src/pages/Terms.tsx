import React from "react";
import { Link } from "react-router-dom";
import { Shield, FileCheck, AlertTriangle, Scale, Cpu, Terminal, ArrowLeft } from "lucide-react";
import { SEO } from "../components/SEO";

export const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220] flex flex-col">
      <SEO
        title="Terms of Use & Acceptable Use Policy — UDT-X"
        description="Terms of Use and Acceptable Use Policy for UDT-X: Authorized lab and enclave telemetry monitoring, data-diode deployment rules, and liability disclaimers."
        canonical="https://udtx.security/terms"
      />

      {/* Navigation Header */}
      <header className="w-full border-b border-[#3FC7D4]/15 bg-[#0B1220]/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-8 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-[#3FC7D4] rounded-lg p-1">
          <div className="w-9 h-9 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center transition-transform group-hover:scale-105">
            <Shield className="w-5 h-5 text-[#3FC7D4]" />
          </div>
          <div>
            <div className="font-display font-bold text-sm tracking-wider text-[#E7ECF5]">UDT-X PLATFORM</div>
            <div className="text-[10px] font-mono text-[#8A95AA]">AUTONOMOUS SIGINT ENCLAVE</div>
          </div>
        </Link>

        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-1.5 text-xs font-mono text-[#8A95AA] hover:text-[#3FC7D4] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
          <Link
            to="/login"
            className="px-3.5 py-1.5 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 text-[#3FC7D4] font-mono text-xs font-bold hover:bg-[#3FC7D4] hover:text-[#0B1220] transition-all"
          >
            Station Login
          </Link>
        </div>
      </header>

      {/* Document Content */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-10">
        <div className="space-y-3 border-b border-[#3FC7D4]/15 pb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#3FC7D4]/10 border border-[#3FC7D4]/30 text-[#3FC7D4] font-mono text-xs">
            <Scale className="w-3.5 h-3.5" />
            <span>STATUTORY & ENTERPRISE LEGAL GOVERNANCE</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-display font-bold tracking-tight text-[#E7ECF5]">
            Terms of Use & Acceptable Use Policy
          </h1>
          <p className="text-sm font-mono text-[#8A95AA]">
            Effective Date: September 11, 2026 | Enclave Version 1.5.0
          </p>
        </div>

        {/* Section 1: Acceptance & Permitted Scope */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            1. Acceptance of Terms & Permitted Scope
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <p>
              By accessing, deploying, or operating the <strong className="text-[#E7ECF5]">UDT-X (Unified Dynamic Threat Identification & Defense Platform)</strong>, you agree to be bound by these Terms of Use.
            </p>
            <p>
              UDT-X is designed strictly as a <strong className="text-[#3FC7D4]">Passive Defense, Lab Simulation, and Security Operations Monitoring System</strong>. It is provided for deployment on networks and infrastructure owned, operated, or explicitly authorized in writing by your organization.
            </p>
          </div>
        </section>

        {/* Section 2: Acceptable Use & Strict Surveillance Prohibition */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#FF4757]" />
            2. Acceptable Use Policy & Strict Prohibitions
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#FF4757]/30 space-y-4 text-sm text-[#8A95AA]">
            <div className="flex items-center gap-2 text-[#FF4757] font-mono text-xs font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span>UNAUTHORIZED NETWORK MONITORING IS STRICTLY PROHIBITED</span>
            </div>
            <p className="leading-relaxed">
              You expressly agree that you shall NOT:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs font-mono text-[#E7ECF5]">
              <li>Deploy UDT-X to monitor, tap, inspect, or intercept network traffic on any network, VLAN, or hardware device without explicit legal authorization from the network owner.</li>
              <li>Use UDT-X for unlawful interception, unauthorized surveillance of individuals, or gathering non-security related personal data.</li>
              <li>Attempt to reverse-engineer data diode unidirectional physical enclaves to inject return-path malicious payloads into monitored segments.</li>
              <li>Circumvent or tamper with the AI Copilot confirmation gates, role clearance checks, or audit trail logging mechanisms.</li>
            </ul>
          </div>
        </section>

        {/* Section 3: Account Responsibilities & Security */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            3. Operator Accounts & Credential Safeguards
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <p>
              Enclave operators are responsible for maintaining the confidentiality of their credentials (argon2id passwords, JWT bearer tokens, and session keys).
            </p>
            <p className="text-xs font-mono">
              All station actions (including attack replays, SIEM exports, and user provisioning) are cryptographically logged with user identity attribution. Sharing analyst credentials across personnel is a direct violation of enclave security policy.
            </p>
          </div>
        </section>

        {/* Section 4: Intellectual Property & Open Source Licensing */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            4. Intellectual Property & License Terms
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <p>
              The core platform, algorithms (TreeSHAP XAI explainers, C2 jitter calculations, DGA Shannon entropy models), and frontend components are distributed under the <strong className="text-[#3FC7D4]">Apache License, Version 2.0</strong>.
            </p>
            <p className="text-xs font-mono">
              All MITRE ATT&CK framework mappings and references remain the copyrighted property of The MITRE Corporation.
            </p>
          </div>
        </section>

        {/* Section 5: Availability Disclaimers & Limitation of Liability */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            5. Disclaimers & Limitation of Liability
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed text-xs">
            <p>
              UDT-X IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.
            </p>
            <p>
              IN NO EVENT SHALL THE AUTHORS, CONTRIBUTORS, OR AFFILIATED RESEARCH INSTITUTIONS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THIS DEFENSE SYSTEM OR LOSS OF NETWORK TELEMETRY DATA.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#3FC7D4]/15 bg-[#0B1220] py-8 px-4 text-center font-mono text-xs text-[#8A95AA] space-y-2">
        <div className="flex justify-center gap-6">
          <Link to="/" className="hover:text-[#3FC7D4] transition-colors">Home</Link>
          <Link to="/faq" className="hover:text-[#3FC7D4] transition-colors">FAQ</Link>
          <Link to="/privacy" className="hover:text-[#3FC7D4] transition-colors">Privacy Policy</Link>
          <Link to="/login" className="hover:text-[#3FC7D4] transition-colors">Enclave Login</Link>
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("open-cookie-preferences"))}
            className="hover:text-[#3FC7D4] transition-colors underline"
          >
            Cookie Preferences
          </button>
        </div>
        <div>© 2026 UDT-X Enclave. Apache License 2.0. DPDP Act 2023 Compliant.</div>
      </footer>
    </div>
  );
};
