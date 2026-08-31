import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Filter,
  Flame,
  Radio,
  Search,
  ShieldAlert,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import type { Severity, ThreatClass } from "../types/soc";

export const LiveMonitorPage: React.FC = () => {
  const { alerts, isConnected } = useLiveStore();
  const [filterClass, setFilterClass] = useState<string>("ALL");
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredAlerts = alerts.filter((a) => {
    if (filterClass !== "ALL" && a.threat_class !== filterClass) return false;
    if (filterSeverity !== "ALL" && a.severity !== filterSeverity) return false;
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
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
          <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
          <span>BUFFERED ALERTS:</span>
          <span className="text-[#3FC7D4] font-bold">{alerts.length}</span>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-[#8A95AA]">
            <Filter className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>CLASS:</span>
          </div>
          <select
            value={filterClass}
            onChange={(e) => setFilterClass(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
          >
            <option value="ALL">ALL CLASSES</option>
            <option value="DDOS">DDOS</option>
            <option value="RECONNAISSANCE">RECONNAISSANCE</option>
            <option value="C2_BEACONING">C2_BEACONING</option>
            <option value="DGA">DGA</option>
            <option value="DNS_TUNNELING">DNS_TUNNELING</option>
            <option value="ENCRYPTED_ANOMALY">ENCRYPTED_ANOMALY</option>
            <option value="EXFILTRATION">EXFILTRATION</option>
          </select>

          <div className="flex items-center gap-2 text-[#8A95AA] ml-2">
            <span>SEVERITY:</span>
          </div>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
          >
            <option value="ALL">ALL SEVERITIES</option>
            <option value="critical">CRITICAL</option>
            <option value="high">HIGH</option>
            <option value="medium">MEDIUM</option>
            <option value="low">LOW</option>
          </select>
        </div>

        {/* Search Field */}
        <div className="relative flex-1 max-w-xs">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#8A95AA]" />
          <input
            type="text"
            placeholder="Search IP, Hash, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] placeholder-[#8A95AA]/60 focus:outline-none focus:border-[#3FC7D4]"
          />
        </div>
      </div>

      {/* Feed Table */}
      <div className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#0B1220] border-b border-[#3FC7D4]/15 text-[#8A95AA]">
              <tr>
                <th className="py-3 px-4">TIMESTAMP</th>
                <th className="py-3 px-4">SEVERITY</th>
                <th className="py-3 px-4">THREAT CLASS</th>
                <th className="py-3 px-4">SOURCE HOST</th>
                <th className="py-3 px-4">DESTINATION HOST</th>
                <th className="py-3 px-4">RISK</th>
                <th className="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#3FC7D4]/10 text-[#E7ECF5]">
              {filteredAlerts.length > 0 ? (
                filteredAlerts.map((alt) => {
                  const sevColor =
                    alt.severity === "critical"
                      ? "#FF4757"
                      : alt.severity === "high"
                      ? "#FF8A3D"
                      : "#3FC7D4";

                  return (
                    <tr
                      key={alt.alert_id}
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
                        {alt.threat_class}
                      </td>
                      <td className="py-3 px-4">{alt.src_ip}</td>
                      <td className="py-3 px-4 text-[#8A95AA]">{alt.dst_ip}</td>
                      <td className="py-3 px-4 font-bold" style={{ color: sevColor }}>
                        {alt.risk_score}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          to={`/alerts/${alt.alert_id}/evidence`}
                          className="text-[11px] text-[#3FC7D4] hover:underline"
                        >
                          EVIDENCE →
                        </Link>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#8A95AA]">
                    No alerts matching active filter parameters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
