import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpDown,
  Calendar,
  ChevronRight,
  Filter,
  Flame,
  Globe,
  Radio,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { EmptyState } from "../components/EmptyState";
import { Tooltip } from "../components/Tooltip";
import { OfflineStateBadge } from "../components/OfflineStateBadge";
import type { Incident } from "../types/soc";

export const IncidentsPage: React.FC = () => {
  const { incidents, alerts, isConnected } = useLiveStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterThreat, setFilterThreat] = useState("ALL");
  const [sortBy, setSortBy] = useState<"risk_desc" | "risk_asc" | "time_desc" | "alerts_desc">("risk_desc");

  // Filtered and sorted incidents
  const filteredIncidents = useMemo(() => {
    return incidents
      .filter((inc) => {
        if (filterThreat !== "ALL") {
          const hasThreat = inc.threat_classes?.includes(filterThreat as any);
          if (!hasThreat && inc.attack_chain !== filterThreat) return false;
        }
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchId = inc.incident_id.toLowerCase().includes(q);
          const matchChain = inc.attack_chain?.toLowerCase().includes(q) || false;
          const matchHost = inc.host?.toLowerCase().includes(q) || false;
          return matchId || matchChain || matchHost;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === "risk_desc") return b.risk_score - a.risk_score;
        if (sortBy === "risk_asc") return a.risk_score - b.risk_score;
        if (sortBy === "alerts_desc") return (b.alert_ids?.length || 0) - (a.alert_ids?.length || 0);
        return new Date(b.window_end).getTime() - new Date(a.window_end).getTime();
      });
  }, [incidents, searchQuery, filterThreat, sortBy]);

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
                isConnected ? "bg-[#FF8A3D] animate-pulse" : "bg-[#8A95AA]"
              }`}
            />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#FF8A3D] uppercase">
              Heuristic & ML Graph Correlation Engine
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Security Incidents Dossier
          </h1>
          <p className="text-xs text-[#8A95AA] mt-0.5">
            Correlated multi-stage security incidents grouped by attack chain and affected hosts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs text-[#8A95AA]">
            <Flame className="w-3.5 h-3.5 text-[#FF8A3D]" />
            <span>TOTAL INCIDENTS:</span>
            <span className="text-[#FF8A3D] font-bold">{incidents.length}</span>
          </div>
          <Link
            to="/app/replay"
            className="px-3.5 py-1.5 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] text-xs font-mono font-bold hover:bg-[#3FC7D4]/25 transition-all flex items-center gap-1.5"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>SIMULATE ATTACK</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Threat Class Filter */}
          <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
            <Filter className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span>THREAT:</span>
            <select
              value={filterThreat}
              onChange={(e) => setFilterThreat(e.target.value)}
              className="bg-[#0B1220] border border-[#3FC7D4]/20 rounded px-2.5 py-1 text-xs text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="ALL">ALL THREATS</option>
              <option value="FULL_KILL_CHAIN">FULL KILL CHAIN</option>
              <option value="DDOS">DDOS</option>
              <option value="C2_BEACONING">C2 BEACONING</option>
              <option value="RECONNAISSANCE">RECONNAISSANCE</option>
              <option value="EXFILTRATION">EXFILTRATION</option>
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
              <option value="risk_desc">Highest Risk First</option>
              <option value="risk_asc">Lowest Risk First</option>
              <option value="time_desc">Latest Activity First</option>
              <option value="alerts_desc">Most Member Alerts</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative min-w-[240px]">
          <Search className="w-3.5 h-3.5 text-[#8A95AA] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search incident ID, host, chain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0B1220] border border-[#3FC7D4]/20 rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#E7ECF5] placeholder-[#8A95AA] focus:outline-none focus:border-[#3FC7D4]"
          />
        </div>
      </div>

      {/* Incidents List or Empty State */}
      {filteredIncidents.length === 0 ? (
        <EmptyState
          icon={Flame}
          title={incidents.length === 0 ? "NO INCIDENTS DETECTED YET" : "NO MATCHING INCIDENTS FOUND"}
          description={
            incidents.length === 0
              ? "The UDT-X graph correlation engine has not detected multi-stage attack patterns yet. Trigger an attack sequence in the Replay Lab to populate the dossier."
              : "No incidents matched your search or filter parameters. Try clearing the filter or searching for another keyword."
          }
          actionLabel={incidents.length === 0 ? "LAUNCH REPLAY LAB →" : "RESET FILTERS"}
          actionTo={incidents.length === 0 ? "/app/replay" : undefined}
          onAction={incidents.length > 0 ? () => { setSearchQuery(""); setFilterThreat("ALL"); } : undefined}
          secondaryActionLabel="VIEW LIVE MONITOR"
          secondaryActionTo="/app/monitor"
          variant={incidents.length === 0 ? "warn" : "default"}
        />
      ) : (
        <div className="space-y-3">
          {filteredIncidents.map((inc, index) => {
            const isHigh = inc.risk_score >= 80;
            const isMed = inc.risk_score >= 50 && inc.risk_score < 80;
            const riskColor = isHigh ? "#FF4757" : isMed ? "#FF8A3D" : "#4CAF7D";
            const memberCount = inc.alert_ids?.length || 0;

            return (
              <motion.div
                key={inc.incident_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(index * 0.04, 0.4) }}
              >
                <Link
                  to={`/app/incidents/${inc.incident_id}`}
                  className="block p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 hover:border-[#3FC7D4]/50 hover:bg-[#1B2540] hover:-translate-y-0.5 active:scale-[0.99] transition-all duration-200 group relative overflow-hidden shadow-lg hover:shadow-[0_0_20px_rgba(63,199,212,0.12)]"
                >
                  {/* Accent Side Bar */}
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1.5 transition-all group-hover:w-2"
                    style={{ backgroundColor: riskColor }}
                  />

                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pl-2">
                    {/* Left Metadata */}
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="font-mono font-bold text-sm text-[#E7ECF5] group-hover:text-[#3FC7D4] transition-colors">
                          {inc.incident_id}
                        </span>

                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider"
                          style={{
                            backgroundColor: `${riskColor}15`,
                            color: riskColor,
                            border: `1px solid ${riskColor}40`,
                          }}
                        >
                          RISK {inc.risk_score.toFixed(1)}
                        </span>

                        {inc.attack_chain && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#3FC7D4]/10 text-[#3FC7D4] border border-[#3FC7D4]/30 font-semibold uppercase">
                            {inc.attack_chain.replace(/_/g, " ")}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-[#8A95AA] font-mono">
                        {inc.host && (
                          <span className="flex items-center gap-1 text-[#E7ECF5]">
                            <Globe className="w-3.5 h-3.5 text-[#3FC7D4]" />
                            Host: <strong className="text-[#3FC7D4]">{inc.host}</strong>
                          </span>
                        )}

                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-[#8A95AA]" />
                          Window: {new Date(inc.window_start).toLocaleTimeString()} – {new Date(inc.window_end).toLocaleTimeString()}
                        </span>

                        <span className="flex items-center gap-1">
                          <ShieldAlert className="w-3.5 h-3.5 text-[#FF8A3D]" />
                          Correlated Alerts: <strong className="text-[#E7ECF5]">{memberCount}</strong>
                        </span>
                      </div>

                      {/* Threat Class Chips */}
                      {inc.threat_classes && inc.threat_classes.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] font-mono text-[#8A95AA]">STAGES:</span>
                          {inc.threat_classes.map((tc) => (
                            <span
                              key={tc}
                              className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA]"
                            >
                              {tc}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-3 shrink-0 self-end lg:self-center">
                      <Tooltip content="Open full kill-chain timeline, affected node topology, and evidence breakdown">
                        <div className="flex items-center gap-1 text-xs font-mono font-bold text-[#3FC7D4] group-hover:translate-x-1 transition-transform">
                          <span>OPEN DOSSIER</span>
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </Tooltip>
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};
