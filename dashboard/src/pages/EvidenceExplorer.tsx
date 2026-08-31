import React from "react";
import {
  Activity,
  ArrowLeft,
  CheckCircle2,
  Database,
  ExternalLink,
  Flame,
  Layers,
  Scale,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import type { Alert } from "../types/soc";

interface EvidenceExplorerProps {
  alertId?: string;
  onBack?: () => void;
}

export const EvidenceExplorerPage: React.FC<EvidenceExplorerProps> = ({
  alertId = "ALT-EXFIL-003",
  onBack,
}) => {
  const { alerts } = useLiveStore();

  const alert: Alert = alerts.find((a) => a.alert_id === alertId) || {
    alert_id: alertId,
    timestamp: new Date().toISOString(),
    flow_id: "flow-exfil-9921",
    src_ip: "192.168.1.105",
    dst_ip: "203.0.113.5",
    threat_class: "EXFILTRATION",
    severity: "critical",
    confidence: 0.98,
    risk_score: 94.5,
    evidence: [
      { label: "Outbound Volume Asymmetry", value: "+5.4σ (8.4 MB vs 120 KB baseline)" },
      { label: "Payload Byte Entropy", value: "7.92 bits/symbol (Encrypted Stream)" },
      { label: "Destination Novelty", value: "1.0 (Unseen External Host)" },
      { label: "TCP Directional Ratio", value: "16.4x Outbound / Inbound" },
    ],
    mitre: ["T1048", "T1071.004"],
    shap_values: [
      { feature: "outbound_byte_ratio", contribution: 0.38 },
      { feature: "payload_shannon_entropy", contribution: 0.28 },
      { feature: "destination_novelty_score", contribution: 0.22 },
      { feature: "flow_duration_ms", contribution: 0.08 },
      { feature: "packet_rate_variance", contribution: -0.04 },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-[#3FC7D4]">
              <ShieldAlert className="w-3.5 h-3.5 text-[#FF4757]" />
              <span className="font-bold uppercase tracking-wider">
                Explainable Forensic Evidence & Model Attribution
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              {alert.alert_id} // {alert.threat_class}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="px-3 py-1.5 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/30 text-[#FF4757] font-bold">
            CONFIDENCE: {(alert.confidence * 100).toFixed(0)}% // RISK: {alert.risk_score}
          </div>
        </div>
      </div>

      {/* Grid: Labeled Forensic Evidence Meters + TreeSHAP Attributions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Heuristic Evidence Parameters */}
        <div className="lg:col-span-6 space-y-4">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
              Mathematical Evidence Metrics & Baseline Deviations
            </h3>

            <div className="space-y-3">
              {alert.evidence.map((ev, i) => (
                <div
                  key={i}
                  className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 flex flex-col justify-between"
                >
                  <span className="text-[11px] font-mono text-[#8A95AA]">{ev.label}</span>
                  <span className="text-sm font-mono font-bold text-[#3FC7D4] mt-1">
                    {String(ev.value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: TreeSHAP Feature Attributions Bar Chart */}
        <div className="lg:col-span-6 space-y-4">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider">
                TreeSHAP Local Feature Contributions
              </h3>
              <span className="text-[10px] font-mono text-[#3FC7D4] bg-[#3FC7D4]/10 px-2 py-0.5 rounded">
                Zero Black-Box
              </span>
            </div>

            <div className="space-y-4">
              {(alert.shap_values || []).map((shap, i) => {
                const isPositive = shap.contribution >= 0;
                const widthPct = Math.min(Math.abs(shap.contribution) * 200, 100);

                return (
                  <div key={i} className="space-y-1 font-mono text-xs">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#E7ECF5]">{shap.feature}</span>
                      <span
                        className="font-bold"
                        style={{ color: isPositive ? "#FF4757" : "#4CAF7D" }}
                      >
                        {isPositive ? "+" : ""}
                        {shap.contribution.toFixed(3)}
                      </span>
                    </div>

                    <div className="w-full h-2 rounded bg-[#0B1220] overflow-hidden flex">
                      {isPositive ? (
                        <div
                          className="h-full bg-[#FF4757] rounded"
                          style={{ width: `${widthPct}%` }}
                        />
                      ) : (
                        <div
                          className="h-full bg-[#4CAF7D] rounded"
                          style={{ width: `${widthPct}%` }}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <p className="text-[11px] font-mono text-[#8A95AA] mt-6 leading-relaxed">
              * Positive values pushed prediction toward malicious classification; negative values
              suppressed anomaly score.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
