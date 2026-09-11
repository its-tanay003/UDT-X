import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Shield, ChevronDown, ChevronUp, HelpCircle, ArrowLeft, ArrowRight, Zap, CheckCircle2, Lock } from "lucide-react";
import { SEO } from "../components/SEO";

interface FAQItem {
  id: string;
  question: string;
  category: "Architecture" | "Security" | "Detection" | "Operations";
  answer: React.ReactNode;
}

export const FAQPage: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<string | null>("faq_1");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const faqs: FAQItem[] = [
    {
      id: "faq_1",
      category: "Architecture",
      question: "What is UDT-X and what is its primary objective?",
      answer: (
        <div className="space-y-2">
          <p>
            UDT-X (Unified Dynamic Threat Identification & Defense Platform) is an autonomous, AI-driven cyber defense platform designed for zero-transmit passive network enclaves.
          </p>
          <p>
            It ingests high-throughput raw telemetry (PCAP, NetFlow, Zeek, Suricata), computes 40+ statistical and entropy features in sub-millisecond sliding windows, detects complex cyber anomalies across 7 specialized rule and ML engines, and correlates multi-stage kill chains in a 3D graph database without ever sending a packet back onto the monitored wire.
          </p>
        </div>
      ),
    },
    {
      id: "faq_2",
      category: "Architecture",
      question: "What does 'unidirectional / passive data diode' mean, and why is it critical?",
      answer: (
        <div className="space-y-2">
          <p>
            A physical data diode uses unidirectional optical hardware (fiber-optic TX coupled to an RX with no return path) to guarantee that information can only flow into the monitoring enclave.
          </p>
          <p>
            This hardware-enforced isolation makes it physically impossible for an adversary or compromised enclave system to inject malicious packets, execute command-and-control return calls, or alter traffic on the protected operational network.
          </p>
        </div>
      ),
    },
    {
      id: "faq_3",
      category: "Operations",
      question: "What data does UDT-X need access to, and does it inspect payload contents?",
      answer: (
        <div className="space-y-2">
          <p>
            UDT-X requires mirrored network packet streams or flow exports (NetFlow/IPFIX, Zeek JSON logs, Suricata EVE).
          </p>
          <p>
            It focuses on packet header metadata, byte distributions, Shannon entropy, Inter-Arrival Time (IAT) periodicity, and TCP flag dynamics. End-user plaintext payloads are not required, preserving absolute privacy and eliminating encryption-bypass requirements.
          </p>
        </div>
      ),
    },
    {
      id: "faq_4",
      category: "Security",
      question: "Is UDT-X safe to run against high-criticality production networks?",
      answer: (
        <div className="space-y-2">
          <p>
            Yes, 100%. Because UDT-X relies on passive network taps and data diodes, it introduces <strong>zero inline latency</strong> and cannot create a single point of failure on the monitored network.
          </p>
          <p>
            Even if the UDT-X processing pipeline is powered down or restarted, the monitored network traffic flows completely unaffected.
          </p>
        </div>
      ),
    },
    {
      id: "faq_5",
      category: "Detection",
      question: "How is UDT-X fundamentally different from traditional IDS/IPS solutions?",
      answer: (
        <div className="space-y-2">
          <p>
            Traditional IDS solutions rely primarily on static signature matching (Snort rules), which fail against zero-day exploits, polymorphic malware, and fast-flux C2 domains.
          </p>
          <p>
            UDT-X integrates a hybrid 7-engine architecture: combining Gaussian EWMA behavioral baselines, TreeSHAP explainable LightGBM anomaly scoring, C2 jitter frequency analysis, and 30-minute rolling Neo4j temporal graph correlation to discover novel, coordinated multi-stage APT campaigns.
          </p>
        </div>
      ),
    },
    {
      id: "faq_6",
      category: "Detection",
      question: "What is TreeSHAP and why does UDT-X use Explainable AI (XAI)?",
      answer: (
        <div className="space-y-2">
          <p>
            TreeSHAP (Tree SHapley Additive exPlanations) is a game-theoretic algorithm that calculates the exact contribution of each network flow feature (e.g. byte asymmetry, Shannon entropy, packet size variance) to an anomaly classification.
          </p>
          <p>
            In high-stakes security operations, "black-box" AI is rejected by analysts. TreeSHAP provides cryptographic feature attribution weights directly in the Evidence Explorer so SOC operators know precisely <em>why</em> an anomaly was flagged.
          </p>
        </div>
      ),
    },
    {
      id: "faq_7",
      category: "Security",
      question: "How does UDT-X comply with India's DPDP Act 2023?",
      answer: (
        <div className="space-y-2">
          <p>
            UDT-X enforces purpose-specific data collection, role-based access control, cryptographic audit logging with 180-day rotation, and explicit consent gates for all non-essential telemetry.
          </p>
          <p>
            Operators have the statutory right to view, rectify, or erase their credentials and session records via the Profile settings and appointed Grievance Officer desk.
          </p>
        </div>
      ),
    },
  ];

  const categories = ["ALL", "Architecture", "Detection", "Security", "Operations"];

  const filteredFaqs = selectedCategory === "ALL"
    ? faqs
    : faqs.filter((f) => f.category === selectedCategory);

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E7ECF5] font-sans selection:bg-[#3FC7D4] selection:text-[#0B1220] flex flex-col">
      <SEO
        title="Frequently Asked Questions (FAQ) — UDT-X"
        description="Detailed answers on UDT-X: Passive optical data-diode architecture, TreeSHAP explainable AI, 7-engine anomaly detection, and DPDP compliance."
        canonical="https://udtx.security/faq"
      />

      {/* Header */}
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
            <span>Home</span>
          </Link>
          <Link
            to="/login"
            className="px-3.5 py-1.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#35B2BE] transition-all shadow-[0_0_12px_rgba(63,199,212,0.3)]"
          >
            Station Login
          </Link>
        </div>
      </header>

      {/* Main FAQ Content */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-10">
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#3FC7D4]/10 border border-[#3FC7D4]/30 text-[#3FC7D4] font-mono text-xs">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>KNOWLEDGE BASE & ARCHITECTURE QUESTIONS</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-display font-bold tracking-tight text-[#E7ECF5]">
            Frequently Asked Questions
          </h1>
          <p className="text-sm font-mono text-[#8A95AA] max-w-2xl mx-auto">
            Technical principles, passive data diode security guarantees, and ML detection pipelines explained.
          </p>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap justify-center gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-lg font-mono text-xs transition-all ${
                selectedCategory === cat
                  ? "bg-[#3FC7D4] text-[#0B1220] font-bold shadow-[0_0_10px_rgba(63,199,212,0.3)]"
                  : "bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] hover:border-[#3FC7D4]/40"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* FAQ Accordion List */}
        <div className="space-y-4">
          {filteredFaqs.map((faq) => {
            const isOpen = openIndex === faq.id;
            return (
              <div
                key={faq.id}
                className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 overflow-hidden transition-all"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : faq.id)}
                  aria-expanded={isOpen}
                  className="w-full p-5 text-left flex items-center justify-between gap-4 hover:bg-[#1B2540] transition-colors focus:outline-none focus:ring-2 focus:ring-[#3FC7D4]"
                >
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono text-[#3FC7D4] uppercase tracking-wider block">
                      {faq.category}
                    </span>
                    <span className="font-display font-bold text-base text-[#E7ECF5]">
                      {faq.question}
                    </span>
                  </div>
                  <div className="w-7 h-7 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/30 flex items-center justify-center shrink-0 text-[#3FC7D4]">
                    {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {isOpen && (
                  <div className="px-5 pb-5 pt-2 border-t border-[#3FC7D4]/10 text-sm text-[#8A95AA] leading-relaxed animate-in fade-in duration-200">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom CTA Card */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-[#131B2E] to-[#1B2540] border border-[#3FC7D4]/30 text-center space-y-4 shadow-2xl">
          <h2 className="text-xl font-display font-bold text-[#E7ECF5]">
            Ready to Inspect Live Network Telemetry?
          </h2>
          <p className="text-xs font-mono text-[#8A95AA] max-w-xl mx-auto">
            Log in to the security command center to test the 7 detection engines, query the AI Copilot, or simulate synthetic APT kill chains in the Replay Lab.
          </p>
          <div className="pt-2">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#3FC7D4] text-[#0B1220] font-mono font-bold text-xs uppercase tracking-wider hover:bg-[#35B2BE] transition-all shadow-[0_0_20px_rgba(63,199,212,0.4)]"
            >
              <span>Access Station Console</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#3FC7D4]/15 bg-[#0B1220] py-8 px-4 text-center font-mono text-xs text-[#8A95AA] space-y-2">
        <div className="flex justify-center gap-6">
          <Link to="/" className="hover:text-[#3FC7D4] transition-colors">Home</Link>
          <Link to="/privacy" className="hover:text-[#3FC7D4] transition-colors">Privacy Policy</Link>
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
