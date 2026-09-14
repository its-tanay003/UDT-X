import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Play,
  Pause,
  Filter,
  Search,
  Zap,
  Radio,
  Clock,
  Flame,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { EmptyState } from "../components/EmptyState";
import { Tooltip } from "../components/Tooltip";
import { OfflineStateBadge } from "../components/OfflineStateBadge";
import type { Severity, ThreatClass } from "../types/soc";

export const LiveMonitorPage: React.FC = () => {
  const { alerts, isConnected } = useLiveStore();
  const [filterClass, setFilterClass] = useState<string>("ALL");
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredAlerts = alerts.filter((a) => {
    if (filterClass !== "ALL" && a.threat_class !== filterClass) return false;
    if (filterSeverity !== "ALL" && a.severity.toLowerCase() !== filterSeverity.toLowerCase()) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        a.src_ip.toLowerCase().includes(q) ||
        a.dst_ip.toLowerCase().includes(q) ||
        a.threat_class.toLowerCase().includes(q) ||
        a.alert_id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Offline Fallback State Notice */}
      <OfflineStateBadge variant="banner" />

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
              Real-time Ingestion Stream // 0-Refresh WebSocket
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Live Telemetry & Alert Monitor
          </h1>
          <p className="text-xs text-[#8A95AA] mt-0.5">
            Continuous zero-latency inspection stream of inbound network flows and detected anomalies.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
          <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
          <span>BUFFERED ALERTS:</span>
          <span className="text-[#3FC7D4] font-bold">{alerts.length}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div id="tour-live-filters" className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 flex flex-wrap items-center justify-between gap-4">
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
            <AlertTriangle className="w-3.5 h-3.5 text-[#FF8A3D]" />
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
        </div>

        {/* Search */}
        <div className="relative min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-[#8A95AA] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search IP, flow, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg pl-9 pr-3 py-1.5 text-xs font-mono text-[#E7ECF5] placeholder-[#8A95AA] focus:outline-none focus:border-[#3FC7D4]"
          />
        </div>
      </div>

      {/* Stream Table or Empty State */}
      {filteredAlerts.length === 0 ? (
        <EmptyState
          icon={Radio}
          title={alerts.length === 0 ? "AWAITING INBOUND TELEMETRY STREAM" : "NO ALERTS MATCHING ACTIVE FILTERS"}
          description={
            alerts.length === 0
              ? "The WebSocket pipeline is active and listening for mirrored packet flows. To populate live telemetry right now, run an attack scenario in the Replay Lab."
              : "No live alerts match your current filter criteria. Try resetting the class or severity filters."
          }
          actionLabel={alerts.length === 0 ? "LAUNCH REPLAY LAB →" : "RESET FILTERS"}
          actionTo={alerts.length === 0 ? "/app/replay" : undefined}
          onAction={alerts.length > 0 ? () => { setSearchQuery(""); setFilterClass("ALL"); setFilterSeverity("ALL"); } : undefined}
          secondaryActionLabel="VIEW INCIDENTS DOSSIER"
          secondaryActionTo="/app/incidents"
          variant={alerts.length === 0 ? "signal" : "default"}
        />
      ) : (
        <div id="tour-live-table" className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 overflow-hidden">
          {/* Mobile Stacked Card View (Hidden on md+) */}
          <div className="md:hidden divide-y divide-[#3FC7D4]/10">
            {filteredAlerts.map((alt, index) => {
              const sevColor =
                alt.severity === "critical"
                  ? "#FF4757"
                  : alt.severity === "high"
                  ? "#FF8A3D"
                  : alt.severity === "medium"
                  ? "#EAB308"
                  : "#4CAF7D";

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
                        backgroundColor: `${sevColor}20`,
                        color: sevColor,
                        border: `1px solid ${sevColor}50`,
                      }}
                    >
                      {alt.severity}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[#3FC7D4] font-semibold">{alt.threat_class}</span>
                    <span className="font-bold" style={{ color: sevColor }}>
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
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-[#8A95AA]">
                      {new Date(alt.timestamp).toLocaleTimeString()}
                    </span>
                    <Link
                      to={`/app/alerts/${alt.alert_id}/evidence`}
                      className="text-xs text-[#3FC7D4] hover:underline font-bold inline-flex items-center gap-1 active:scale-[0.97] transition-all"
                    >
                      <span>INSPECT EVIDENCE</span>
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
              <thead className="bg-[#0B1220] border-b border-[#3FC7D4]/15 text-[#8A95AA] uppercase text-[10px] tracking-wider select-none">
                <tr>
                  <th className="py-3 px-4">TIMESTAMP</th>
                  <th className="py-3 px-4">SEVERITY</th>
                  <th className="py-3 px-4">THREAT CLASS</th>
                  <th className="py-3 px-4">SOURCE HOST</th>
                  <th className="py-3 px-4">DESTINATION HOST</th>
                  <th className="py-3 px-4">
                    <Tooltip content="Composite hazard score based on baseline deviation and confidence" code="RISK">
                      <span className="cursor-help border-b border-dashed border-[#8A95AA]">RISK</span>
                    </Tooltip>
                  </th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3FC7D4]/10 text-[#E7ECF5]">
                {filteredAlerts.map((alt, index) => {
                  const sevColor =
                    alt.severity === "critical"
                      ? "#FF4757"
                      : alt.severity === "high"
                      ? "#FF8A3D"
                      : alt.severity === "medium"
                      ? "#EAB308"
                      : "#4CAF7D";

                  return (
                    <motion.tr
                      key={alt.alert_id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: Math.min(index * 0.03, 0.4) }}
                      className="hover:bg-[#1B2540]/50 transition-colors group"
                    >
                      <td className="py-3 px-4 text-[#8A95AA]">
                        {new Date(alt.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                          style={{
                            backgroundColor: `${sevColor}20`,
                            color: sevColor,
                            border: `1px solid ${sevColor}50`,
                          }}
                        >
                          {alt.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-bold text-[#E7ECF5]">
                        <Tooltip content={`Threat category: ${alt.threat_class}`}>
                          <span className="cursor-help">{alt.threat_class}</span>
                        </Tooltip>
                      </td>
                      <td className="py-3 px-4">{alt.src_ip}</td>
                      <td className="py-3 px-4 text-[#8A95AA]">{alt.dst_ip}</td>
                      <td className="py-3 px-4 font-bold" style={{ color: sevColor }}>
                        {alt.risk_score.toFixed(1)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          to={`/app/alerts/${alt.alert_id}/evidence`}
                          className="text-[#3FC7D4] hover:underline font-bold inline-flex items-center gap-1 active:scale-[0.97] transition-all"
                        >
                          <span>INSPECT</span>
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
