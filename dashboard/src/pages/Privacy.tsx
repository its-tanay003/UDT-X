import React from "react";
import { Link } from "react-router-dom";
import { Shield, Lock, Eye, FileText, Database, UserCheck, Mail, ArrowLeft } from "lucide-react";
import { SEO } from "../components/SEO";

export const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220] flex flex-col">
      <SEO
        title="Privacy Policy | DPDP Act 2023 Compliance — UDT-X"
        description="Official Privacy Policy and Data Fiduciary disclosure for the UDT-X Platform under India's Digital Personal Data Protection (DPDP) Act 2023 & DPDP Rules 2025."
        canonical="https://udtx.security/privacy"
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
            <Lock className="w-3.5 h-3.5" />
            <span>STATUTORY COMPLIANCE: DPDP ACT 2023 & DPDP RULES 2025</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-display font-bold tracking-tight text-[#E7ECF5]">
            Privacy Policy & Data Fiduciary Notice
          </h1>
          <p className="text-sm font-mono text-[#8A95AA]">
            Effective Date: September 11, 2026 | Last Revised: v1.5.0 Enclave Release
          </p>
        </div>

        {/* Section 1: Data Fiduciary Identity */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            1. Identity of the Data Fiduciary
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <p>
              This Privacy Policy is issued by the <strong className="text-[#E7ECF5]">UDT-X Project Enclave & Autonomous Defense Research Consortium</strong> (hereafter <strong className="text-[#E7ECF5]">"Data Fiduciary"</strong>, "we", "us", or "our").
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 font-mono text-xs">
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                <span className="text-[#3FC7D4] block font-bold">DATA PROTECTION OFFICER (DPO):</span>
                <span className="text-[#E7ECF5]">Grievance & Privacy Desk</span>
              </div>
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                <span className="text-[#3FC7D4] block font-bold">OFFICIAL GRIEVANCE CONTACT:</span>
                <span className="text-[#E7ECF5]">privacy-enclave@udtx.security</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Specific Categories of Personal Data Collected */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            2. Categories of Personal Data & Specified Purpose
          </h2>
          <p className="text-sm text-[#8A95AA] leading-relaxed">
            Under Section 6 of the DPDP Act 2023, data is collected solely for explicit, specific, and lawful purposes without unbundled consent clauses:
          </p>

          <div className="overflow-x-auto rounded-xl border border-[#3FC7D4]/20 bg-[#131B2E]">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#0B1220] text-[#3FC7D4] border-b border-[#3FC7D4]/20">
                <tr>
                  <th className="p-3.5">Category of Data</th>
                  <th className="p-3.5">Data Elements</th>
                  <th className="p-3.5">Specified Purpose</th>
                  <th className="p-3.5">Legal Basis</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3FC7D4]/10 text-[#8A95AA]">
                <tr>
                  <td className="p-3.5 text-[#E7ECF5] font-bold">Account & Credentials</td>
                  <td className="p-3.5">Analyst Email, Display Call-Sign, Argon2id Password Hash</td>
                  <td className="p-3.5">Authentication & station access control to the security enclave</td>
                  <td className="p-3.5 text-[#4CAF7D]">Contractual & Security Necessity</td>
                </tr>
                <tr>
                  <td className="p-3.5 text-[#E7ECF5] font-bold">Enclave Audit Logs</td>
                  <td className="p-3.5">Timestamped operator action history, simulation triggers, SIEM exports</td>
                  <td className="p-3.5">Cryptographic accountability, non-repudiation, and audit compliance</td>
                  <td className="p-3.5 text-[#4CAF7D]">Legal Obligation & Audit Duty</td>
                </tr>
                <tr>
                  <td className="p-3.5 text-[#E7ECF5] font-bold">Station Preferences</td>
                  <td className="p-3.5">Audio signal alerts, particle rendering density, UI theme mode</td>
                  <td className="p-3.5">Persisting custom console settings across operator sessions</td>
                  <td className="p-3.5 text-[#3FC7D4]">Freely Given Consent</td>
                </tr>
                <tr>
                  <td className="p-3.5 text-[#E7ECF5] font-bold">First-Party Telemetry</td>
                  <td className="p-3.5">Cookieless client latency, page route hits (anonymous aggregate)</td>
                  <td className="p-3.5">Performance optimization and SLA wire rate tuning</td>
                  <td className="p-3.5 text-[#3FC7D4]">Consent-Gated (Opt-in only)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 3: Passive Data Diode & Enclave Isolation */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            3. Network Telemetry & Zero-Surveillance Architecture
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <p>
              UDT-X operates as a <strong className="text-[#3FC7D4]">Passive, Unidirectional Optical Tap Enclave</strong>. It inspects network packet headers (IP, TCP/UDP metadata, entropy attributes) for cyber anomaly detection.
            </p>
            <p className="text-xs">
              <strong className="text-[#FF8A3D]">Important Distinction:</strong> Network flow metadata processed in the detection pipeline does not constitute end-user personal data under the DPDP Act unless bound to an enclave operator identity. Raw packet payloads are never stored, decrypted, or exported to external third parties.
            </p>
          </div>
        </section>

        {/* Section 4: Data Retention & Erasure */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            4. Data Retention and Erasure Schedule
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA] leading-relaxed">
            <ul className="list-disc pl-5 space-y-2 text-xs font-mono">
              <li>
                <strong className="text-[#E7ECF5]">Account Data:</strong> Retained for the active lifecycle of the enclave operator. Upon account de-provisioning by an administrator, personal credentials are deleted within 30 days.
              </li>
              <li>
                <strong className="text-[#E7ECF5]">Audit Trail Logs:</strong> Maintained in cryptographic append-only logs for 180 days for statutory security verification before automatic rotation.
              </li>
              <li>
                <strong className="text-[#E7ECF5]">Local Browser State:</strong> Cached items in IndexedDB and localStorage (offline staged actions) remain under full local control and can be purged instantly via browser settings.
              </li>
            </ul>
          </div>
        </section>

        {/* Section 5: Rights of Data Principals */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            5. Rights of the Data Principal (Under DPDP Act 2023)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-1.5">
              <span className="text-[#3FC7D4] font-bold block">RIGHT TO ACCESS & SUMMARY</span>
              <p className="text-[#8A95AA]">
                Operators may view all stored profile information directly in the Profile settings console at any time.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-1.5">
              <span className="text-[#3FC7D4] font-bold block">RIGHT TO CORRECTION & ERASURE</span>
              <p className="text-[#8A95AA]">
                Operators can update call-signs and passwords in real-time or request full account erasure via the DPO desk.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-1.5">
              <span className="text-[#3FC7D4] font-bold block">RIGHT TO GRIEVANCE REDRESSAL</span>
              <p className="text-[#8A95AA]">
                Submit formal grievances to our appointed DPO with guaranteed response and resolution within 7 working days.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-1.5">
              <span className="text-[#3FC7D4] font-bold block">RIGHT TO NOMINATE</span>
              <p className="text-[#8A95AA]">
                Designate a proxy representative in the event of incapacity or death through formal enterprise administrative channels.
              </p>
            </div>
          </div>
        </section>

        {/* Section 6: Grievance Redressal Mechanism */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5] flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
            6. Grievance Officer & Contact Information
          </h2>
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3 text-sm text-[#8A95AA]">
            <p>
              If you have any questions, concerns, or requests regarding this Privacy Policy or wish to exercise your statutory rights under the DPDP Act 2023, contact our designated Grievance Officer:
            </p>
            <div className="font-mono text-xs p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 space-y-1">
              <div><strong className="text-[#3FC7D4]">Designation:</strong> Data Protection & Enclave Grievance Officer</div>
              <div><strong className="text-[#3FC7D4]">Entity:</strong> UDT-X Cybersecurity Research Enclave</div>
              <div><strong className="text-[#3FC7D4]">Electronic Mail:</strong> <a href="mailto:privacy-enclave@udtx.security" className="text-[#3FC7D4] underline">privacy-enclave@udtx.security</a></div>
              <div><strong className="text-[#3FC7D4]">Response Time:</strong> Within 7 Business Days (as prescribed under DPDP Rules 2025)</div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#3FC7D4]/15 bg-[#0B1220] py-8 px-4 text-center font-mono text-xs text-[#8A95AA] space-y-2">
        <div className="flex justify-center gap-6">
          <Link to="/" className="hover:text-[#3FC7D4] transition-colors">Home</Link>
          <Link to="/faq" className="hover:text-[#3FC7D4] transition-colors">FAQ</Link>
          <Link to="/terms" className="hover:text-[#3FC7D4] transition-colors">Terms of Use</Link>
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
