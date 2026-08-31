import React, { useState, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ChevronRight,
  Filter,
  Flame,
  Radio,
  Search,
  Shield,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import type { Alert, Severity, ThreatClass } from "../types/soc";

interface LiveMonitorProps {
  onSelectAlert?: (alertId: string) => void;
  onSelectIncident?: (incidentId: string) => void;
}

export const LiveMonitorPage: React.FC<LiveMonitorProps> = ({
  onSelectAlert,
  onSelectIncident,
}) => {
  const { alerts, isConnected } = useLiveStore();
  const [selectedThreatClass, setSelectedThreatClass] = useState<string>("ALL");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Default demonstration telemetry if store is empty
  const defaultDemonstrationAlerts: Alert[] = useMemo(
    () => [
      {
        alert_id: "ALT-EXFIL-003",
        timestamp: new Date(Date.now() - 30000).toISOString(),
        flow_id: "flow-exfil-9921",
        src_ip: "192.168.1.105",
        dst_ip: "203.0.113.5",
        threat_class: "EXFILTRATION",
        severity: "critical",
        confidence: 0.98,
        risk_score: 94.5,
        evidence: [
          { label: "Outbound Volume Spike", value: "8.4 MB (+5.4σ)" },
          { label: "Destination Novelty", value: "First Encounter" },
        ],
        mitre: ["T1048"],
      },
      {
        alert_id: "ALT-BEACON-002",
        timestamp: new Date(Date.now() - 90000).toISOString(),
        flow_id: "flow-beacon-4412",
        src_ip: "192.168.1.105",
        dst_ip: "198.51.100.22",
        threat_class: "C2_BEACONING",
        severity: "high",
        confidence: 0.94,
        risk_score: 88.0,
        evidence: [
          { label: "IAT Periodicity", value: "60.02s (Jitter 0.04s)" },
          { label: "Payload Autocorrelation", value: "0.982" },
        ],
        mitre: ["T1071.004"],
      },
      {
        alert_id: "ALT-RECON-001",
        timestamp: new Date(Date.now() - 240000).toISOString(),
        flow_id: "flow-recon-1033",
        src_ip: "192.168.1.105",
        dst_ip: "10.0.0.1",
        threat_class: "RECONNAISSANCE",
        severity: "medium",
        confidence: 0.89,
        risk_score: 65.0,
        evidence: [
          { label: "SYN Probe Ratio", value: "0.96 (120 ports/sec)" },
        ],
        mitre: ["T1046"],
      },
    ],
    []
  );

  const displayAlerts = alerts.length > 0 ? alerts : defaultDemonstrationAlerts;

  // Filter pipeline
  const filteredAlerts = useMemo(() => {
    return displayAlerts.filter((a) => {
      if (selectedThreatClass !== "ALL" && a.threat_class !== selectedThreatClass)
        return false;
      if (selectedSeverity !== "ALL" && a.severity !== selectedSeverity)
        return false;
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesIp =
          a.src_ip.toLowerCase().includes(query) ||
          a.dst_ip.toLowerCase().includes(query);
        const matchesId = a.alert_id.toLowerCase().includes(query);
        if (!matchesIp && !matchesId) return false;
      }
      return true;
    });
  }, [displayAlerts, selectedThreatClass, selectedSeverity, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header & Status Indicator */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Live Stream Engine // WebSocket /ws/live
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Live Telemetry Alert Monitor
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs text-[#8A95AA]">
            <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
            <span>ACTIVE ALERTS:</span>
            <span className="text-[#E7ECF5] font-bold">{filteredAlerts.length}</span>
          </div>
        </div>
      </div>

      {/* Filter Surface Controls */}
      <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Threat Class Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#8A95AA]">THREAT:</span>
            <select
              value={selectedThreatClass}
              onChange={(e) => setSelectedThreatClass(e.target.value)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg px-3 py-1.5 text-xs font-mono text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="ALL">ALL THREAT CLASSES</option>
              <option value="DDOS">DDOS</option>
              <option value="RECONNAISSANCE">RECONNAISSANCE</option>
              <option value="C2_BEACONING">C2_BEACONING</option>
              <option value="DGA">DGA</option>
              <option value="DNS_TUNNELING">DNS_TUNNELING</option>
              <option value="ENCRYPTED_ANOMALY">ENCRYPTED_ANOMALY</option>
              <option value="EXFILTRATION">EXFILTRATION</option>
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-[#8A95AA]">SEVERITY:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg px-3 py-1.5 text-xs font-mono text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="ALL">ALL SEVERITIES</option>
              <option value="critical">CRITICAL</option>
              <option value="high">HIGH</option>
              <option value="medium">MEDIUM</option>
              <option value="low">LOW</option>
            </select>
          </div>
        </div>

        {/* IP Search Filter */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#8A95AA] absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Host IP or Alert ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg pl-8 pr-3 py-1.5 text-xs font-mono text-[#E7ECF5] placeholder-[#8A95AA]/60 focus:outline-none focus:border-[#3FC7D4] w-64"
          />
        </div>
      </div>

      {/* Feed Table */}
      <div className="rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#0B1220] text-[#8A95AA] border-b border-[#3FC7D4]/15 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">TIMESTAMP</th>
                <th className="py-3 px-4">ALERT ID</th>
                <th className="py-3 px-4">THREAT CLASS</th>
                <th className="py-3 px-4">SOURCE HOST $\rightarrow$ TARGET</th>
                <th className="py-3 px-4">RISK SCORE</th>
                <th className="py-3 px-4">SEVERITY</th>
                <th className="py-3 px-4">MITRE</th>
                <th className="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#3FC7D4]/10">
              {filteredAlerts.map((alert) => {
                const isCrit = alert.severity === "critical";
                const isHigh = alert.severity === "high";
                const isMed = alert.severity === "medium";

                const badgeBg = isCrit
                  ? "bg-[#FF4757]/15 text-[#FF4757] border-[#FF4757]/30"
                  : isHigh
                  ? "bg-[#FF8A3D]/15 text-[#FF8A3D] border-[#FF8A3D]/30"
                  : isMed
                  ? "bg-[#3FC7D4]/15 text-[#3FC7D4] border-[#3FC7D4]/30"
                  : "bg-[#4CAF7D]/15 text-[#4CAF7D] border-[#4CAF7D]/30";

                return (
                  <tr
                    key={alert.alert_id}
                    className="hover:bg-[#1B2540] transition-colors cursor-pointer group"
                    onClick={() => onSelectAlert && onSelectAlert(alert.alert_id)}
                  >
                    <td className="py-3 px-4 text-[#8A95AA] whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-[#E7ECF5] font-bold">
                      {alert.alert_id}
                    </td>
                    <td className="py-3 px-4 text-[#E7ECF5] font-bold">
                      {alert.threat_class}
                    </td>
                    <td className="py-3 px-4 text-[#E7ECF5] whitespace-nowrap">
                      <span className="text-[#3FC7D4]">{alert.src_ip}</span>
                      <span className="text-[#8A95AA] mx-2">→</span>
                      <span>{alert.dst_ip}</span>
                    </td>
                    <td className="py-3 px-4 font-bold" style={{ color: isCrit ? "#FF4757" : isHigh ? "#FF8A3D" : "#3FC7D4" }}>
                      {alert.risk_score.toFixed(1)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${badgeBg}`}
                      >
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#8A95AA]">
                      {alert.mitre.join(", ") || "—"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAlert && onSelectAlert(alert.alert_id);
                        }}
                        className="p-1 rounded bg-[#0B1220] border border-[#3FC7D4]/20 text-[#3FC7D4] group-hover:border-[#3FC7D4] transition-colors"
                      >
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
