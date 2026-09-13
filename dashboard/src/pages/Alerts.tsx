import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  Download,
  Filter,
  Layers,
  Radio,
  Search,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { EmptyState } from "../components/EmptyState";
import { Tooltip } from "../components/Tooltip";
import type { Severity, ThreatClass } from "../types/soc";

export const AlertsPage: React.FC = () => {
  const { alerts, isConnected } = useLiveStore();
  const [filterClass, setFilterClass] = useState<string>("ALL");
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"risk_desc" | "risk_asc" | "time_desc" | "time_asc">("time_desc");
  const [isExporting, setIsExporting] = useState<string | null>(null);

  // Filtered & sorted alerts list
  const filteredAlerts = useMemo(() => {
    return alerts
      .filter((a) => {
        if (filterClass !== "ALL" && a.threat_class !== filterClass) return false;
        if (filterSeverity !== "ALL" && a.severity !== filterSeverity) return false;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchSrc = a.src_ip.toLowerCase().includes(q);
          const matchDst = a.dst_ip.toLowerCase().includes(q);
          const matchClass = a.threat_class.toLowerCase().includes(q);
          const matchId = a.alert_id.toLowerCase().includes(q);
          const matchMitre = a.mitre?.some((m) => m.toLowerCase().includes(q)) || false;
          return matchSrc || matchDst || matchClass || matchId || matchMitre;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "risk_desc") return b.risk_score - a.risk_score;
        if (sortBy === "risk_asc") return a.risk_score - b.risk_score;
        if (sortBy === "time_asc") return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });
  }, [alerts, filterClass, filterSeverity, searchQuery, sortBy]);

  // Export alerts in CEF or Syslog RFC 5424 formats
  const handleExport = async (format: "cef" | "syslog") => {
    try {
      setIsExporting(format);
      const res = await fetch(`http://localhost:8000/alerts/export?format=${format}&limit=500`);
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `udtx_alerts_export_${Date.now()}.${format === "cef" ? "cef" : "log"}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setIsExporting(null);
    }
  };

  const getSeverityStyle = (sev: Severity) => {
    switch (sev) {
      case "critical":
        return { color: "#FF4757", bg: "rgba(255, 71, 87, 0.15)", border: "rgba(255, 71, 87, 0.4)" };
      case "high":
        return { color: "#FF8A3D", bg: "rgba(255, 138, 61, 0.15)", border: "rgba(255, 138, 61, 0.4)" };
      case "medium":
        return { color: "#EAB308", bg: "rgba(234, 179, 8, 0.15)", border: "rgba(234, 179, 8, 0.4)" };
      default:
        return { color: "#4CAF7D", bg: "rgba(76, 175, 125, 0.15)", border: "rgba(76, 175, 125, 0.4)" };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? "bg-[#3FC7D4] animate-pulse" : "bg-[#8A95AA]"
              }`}
            />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Heuristic & TreeSHAP Anomaly Engine
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Alerts & Evidence Explorer
          </h1>
          <p className="text-xs text-[#8A95AA] mt-0.5">
            Scored anomaly log from UDT-X passive detection engines with full SIEM export capability.
          </p>
        </div>

        {/* SIEM Export & Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs text-[#8A95AA]">
            <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
            <span>BUFFERED:</span>
            <span className="text-[#3FC7D4] font-bold">{alerts.length}</span>
          </div>

          <Tooltip content="Export all alerts in ArcSight Common Event Format (CEF) for SIEM ingestion">
            <button
              onClick={() => handleExport("cef")}
              disabled={isExporting !== null}
              className="px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/30 hover:border-[#3FC7D4] text-[#3FC7D4] text-xs font-mono font-bold transition-all flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting === "cef" ? "EXPORTING..." : "EXPORT CEF"}</span>
            </button>
          </Tooltip>

          <Tooltip content="Export alerts as RFC 5424 formatted Syslog records">
            <button
              onClick={() => handleExport("syslog")}
              disabled={isExporting !== null}
              className="px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/30 hover:border-[#3FC7D4] text-[#8A95AA] hover:text-[#E7ECF5] text-xs font-mono transition-all flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting === "syslog" ? "EXPORTING..." : "EXPORT SYSLOG"}</span>
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Filters, Sorting and Search Bar */}
      <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Class Filter */}
          <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
            <Filter className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>CLASS:</span>
            <select
              value={filterClass}
              onChange={(e) => setFilterClass(e.target.value)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded px-2.5 py-1 text-xs text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="ALL">ALL CLASSES</option>
              <option value="DDOS">DDOS</option>
              <option value="C2_BEACONING">C2 BEACONING</option>
              <option value="RECONNAISSANCE">RECONNAISSANCE</option>
              <option value="DGA">DGA</option>
              <option value="DNS_TUNNELING">DNS TUNNELING</option>
              <option value="ENCRYPTED_ANOMALY">ENCRYPTED ANOMALY</option>
              <option value="EXFILTRATION">EXFILTRATION</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
            <span>SEVERITY:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded px-2.5 py-1 text-xs text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="ALL">ALL SEVERITIES</option>
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
            <ArrowUpDown className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>SORT:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded px-2.5 py-1 text-xs text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="time_desc">Newest First</option>
              <option value="time_asc">Oldest First</option>
              <option value="risk_desc">Highest Risk Score</option>
              <option value="risk_asc">Lowest Risk Score</option>
            </select>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-[#8A95AA] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search IP, alert ID, MITRE..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#E7ECF5] placeholder-[#8A95AA] focus:outline-none focus:border-[#3FC7D4]"
          />
        </div>
      </div>

      {/* Alerts Table or Empty State */}
      {filteredAlerts.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title={alerts.length === 0 ? "NO ALERTS DETECTED YET" : "NO MATCHING ALERTS FOUND"}
          description={
            alerts.length === 0
              ? "The live telemetry stream is listening for inbound traffic anomalies across passive mirror taps. You can trigger an attack simulation in Replay Lab."
              : "No alerts match your current filter parameters. Try selecting 'ALL CLASSES' or resetting the search."
          }
          actionLabel={alerts.length === 0 ? "RUN REPLAY ATTACK SIMULATION →" : "RESET FILTERS"}
          actionTo={alerts.length === 0 ? "/app/replay" : undefined}
          onAction={alerts.length > 0 ? () => { setSearchQuery(""); setFilterClass("ALL"); setFilterSeverity("ALL"); } : undefined}
          secondaryActionLabel="VIEW LIVE MONITOR"
          secondaryActionTo="/app/monitor"
        />
      ) : (
        <div className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 overflow-hidden">
          {/* Mobile Stacked Card View (Hidden on md+) */}
          <div className="md:hidden divide-y divide-[#3FC7D4]/10">
            {filteredAlerts.map((alt, index) => {
              const sevStyle = getSeverityStyle(alt.severity);

              return (
                <motion.div
                  key={alt.alert_id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: Math.min(index * 0.03, 0.45) }}
                  className="p-4 space-y-3 font-mono text-xs hover:bg-[#1B2540]/40 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#E7ECF5]">{alt.alert_id}</span>
                    <span
                      className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                      style={{
                        backgroundColor: sevStyle.bg,
                        color: sevStyle.color,
                        border: `1px solid ${sevStyle.border}`,
                      }}
                    >
                      {alt.severity}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[#3FC7D4] font-semibold">{alt.threat_class}</span>
                    <span className="font-bold" style={{ color: sevStyle.color }}>
                      RISK {alt.risk_score.toFixed(1)}
                    </span>
                  </div>

                  <div className="text-[11px] text-[#8A95AA] flex flex-col gap-1 bg-[#0B1220] p-2.5 rounded border border-[#3FC7D4]/10">
                    <div className="flex justify-between">
                      <span>SRC:</span>
                      <span className="text-[#E7ECF5]">{alt.src_ip}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>DST:</span>
                      <span className="text-[#8A95AA]">{alt.dst_ip}</span>
                    </div>
                    {alt.mitre && alt.mitre.length > 0 && (
                      <div className="flex items-center justify-between pt-1 border-t border-[#3FC7D4]/10">
                        <span>MITRE:</span>
                        <span className="text-[#3FC7D4]">{alt.mitre.join(", ")}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-[#8A95AA]">
                      {new Date(alt.timestamp).toLocaleTimeString()}
                    </span>
                    <Link
                      to={`/alerts/${alt.alert_id}/evidence`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] text-[11px] font-bold hover:bg-[#3FC7D4]/25 hover:border-[#3FC7D4] active:scale-[0.97] transition-all"
                    >
                      <span>EVIDENCE</span>
                      <span>→</span>
                    </Link>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Desktop/Tablet Table View (Hidden on mobile) */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#0B1220] text-[#8A95AA] border-b border-[#3FC7D4]/15 uppercase text-[10px] tracking-wider select-none">
                <tr>
                  <th className="py-3 px-4">TIMESTAMP</th>
                  <th className="py-3 px-4">ALERT ID</th>
                  <th className="py-3 px-4">SEVERITY</th>
                  <th className="py-3 px-4">THREAT CLASS</th>
                  <th className="py-3 px-4">SOURCE IP</th>
                  <th className="py-3 px-4">DESTINATION IP</th>
                  <th className="py-3 px-4">
                    <Tooltip content="Composite risk score (0-100) calculated from baseline deviation and confidence" code="RISK">
                      <span className="cursor-help border-b border-dashed border-[#8A95AA]">RISK SCORE</span>
                    </Tooltip>
                  </th>
                  <th className="py-3 px-4">
                    <Tooltip content="Mapped MITRE ATT&CK enterprise techniques" code="ATT&CK">
                      <span className="cursor-help border-b border-dashed border-[#8A95AA]">MITRE</span>
                    </Tooltip>
                  </th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3FC7D4]/10">
                {filteredAlerts.map((alt, index) => {
                  const sevStyle = getSeverityStyle(alt.severity);

                  return (
                    <motion.tr
                      key={alt.alert_id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: Math.min(index * 0.03, 0.4) }}
                      className="hover:bg-[#1B2540]/60 transition-colors group"
                    >
                      <td className="py-3 px-4 text-[#8A95AA]">
                        {new Date(alt.timestamp).toLocaleTimeString()}
                      </td>

                      <td className="py-3 px-4 font-bold text-[#E7ECF5]">
                        <Link
                          to={`/alerts/${alt.alert_id}/evidence`}
                          className="hover:text-[#3FC7D4] transition-colors"
                        >
                          {alt.alert_id}
                        </Link>
                      </td>

                      <td className="py-3 px-4">
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                          style={{
                            backgroundColor: sevStyle.bg,
                            color: sevStyle.color,
                            border: `1px solid ${sevStyle.border}`,
                          }}
                        >
                          {alt.severity}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-bold text-[#E7ECF5]">
                        <Tooltip content={`Threat Category: ${alt.threat_class}`}>
                          <span className="px-2 py-0.5 rounded bg-[#0B1220] border border-[#3FC7D4]/20 text-[#3FC7D4] text-[11px]">
                            {alt.threat_class}
                          </span>
                        </Tooltip>
                      </td>

                      <td className="py-3 px-4 text-[#E7ECF5]">{alt.src_ip}</td>
                      <td className="py-3 px-4 text-[#8A95AA]">{alt.dst_ip}</td>

                      <td className="py-3 px-4 font-bold" style={{ color: sevStyle.color }}>
                        {alt.risk_score.toFixed(1)}
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {alt.mitre && alt.mitre.length > 0 ? (
                            alt.mitre.slice(0, 2).map((m) => (
                              <Tooltip key={m} content={`MITRE ATT&CK Technique ID: ${m}`} code={m}>
                                <span className="px-1.5 py-0.5 rounded bg-[#0B1220] text-[#8A95AA] text-[10px] border border-[#3FC7D4]/10 cursor-help hover:border-[#3FC7D4]/40 hover:text-[#E7ECF5] transition-colors">
                                  {m}
                                </span>
                              </Tooltip>
                            ))
                          ) : (
                            <span className="text-[#8A95AA] text-[10px]">—</span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <Link
                          to={`/alerts/${alt.alert_id}/evidence`}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded bg-[#3FC7D4]/10 border border-[#3FC7D4]/20 text-[#3FC7D4] text-xs font-bold hover:bg-[#3FC7D4]/25 hover:border-[#3FC7D4] active:scale-[0.97] transition-all"
                        >
                          <span>EVIDENCE</span>
                          <span>→</span>
                        </Link>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
