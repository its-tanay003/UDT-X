import React, { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  BarChart2,
  Calendar,
  Flame,
  PieChart,
  Radio,
  RefreshCw,
  Shield,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { fetchThreatStats, type ThreatStatsResponse } from "../lib/api/threats";
import { SonarRadialChart } from "../components/SonarRadialChart";

interface ThreatCenterProps {
  onBack?: () => void;
  onSelectThreat?: (threatClass: string) => void;
}

export const ThreatCenterPage: React.FC<ThreatCenterProps> = ({
  onBack,
  onSelectThreat,
}) => {
  const [timeRange, setTimeRange] = useState<string>("24h");
  const [stats, setStats] = useState<ThreatStatsResponse | null>(null);
  const [selectedClass, setSelectedClass] = useState<string | null>("DDOS");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadStats = async () => {
      setIsLoading(true);
      const data = await fetchThreatStats(timeRange, "http://localhost:8000");
      setStats(data);
      setIsLoading(false);
    };
    loadStats();
  }, [timeRange]);

  const selectedItem = stats?.classes.find((c) => c.threat_class === selectedClass);

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
              <Radio className="w-3.5 h-3.5 text-[#3FC7D4] animate-pulse" />
              <span className="font-bold uppercase tracking-wider">
                Threat Intelligence Analytics & Distribution
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              Threat Center // Radial Sonar Analytics
            </h1>
          </div>
        </div>

        {/* Time Filter Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs">
          {["1h", "24h", "7d", "30d"].map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-3 py-1 rounded transition-colors ${
                timeRange === r
                  ? "bg-[#3FC7D4] text-[#0B1220] font-bold"
                  : "text-[#8A95AA] hover:text-[#E7ECF5]"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Grid: Custom D3 Sonar Sweep Chart + Detailed Breakdown Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* D3 Sonar Sweep Radar (Signature Element #2) */}
        <div className="lg:col-span-7 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col items-center justify-between">
          <div className="flex items-center justify-between w-full mb-2">
            <span className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider">
              D3 Sonar Sweep Radial Distribution
            </span>
            <span className="text-[11px] font-mono text-[#8A95AA]">
              TOTAL: {stats?.total_alerts.toLocaleString()} ALERTS
            </span>
          </div>

          <SonarRadialChart
            data={stats?.classes || []}
            selectedClass={selectedClass}
            onSelectClass={(tc) => setSelectedClass(tc)}
            width={380}
            height={380}
          />

          <span className="text-[11px] font-mono text-[#8A95AA]">
            Click any sonar wedge segment to view forensic telemetry drilldown.
          </span>
        </div>

        {/* Detailed Class Drilldown Panel */}
        <div className="lg:col-span-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 space-y-5">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider">
            Threat Profile Drilldown
          </h3>

          {selectedItem ? (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                <span className="text-[10px] text-[#8A95AA] uppercase">THREAT CLASS</span>
                <h4 className="text-xl font-display font-bold text-[#3FC7D4] mt-1">
                  {selectedItem.threat_class}
                </h4>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-[#8A95AA]">Event Count:</span>
                  <span className="font-bold text-[#E7ECF5]">
                    {selectedItem.count.toLocaleString()}
                  </span>
                </div>
                <div className="mt-1.5 flex items-center justify-between">
                  <span className="text-[#8A95AA]">Average Risk Score:</span>
                  <span
                    className="font-bold"
                    style={{
                      color:
                        selectedItem.avg_risk > 85
                          ? "#FF4757"
                          : selectedItem.avg_risk > 70
                          ? "#FF8A3D"
                          : "#3FC7D4",
                    }}
                  >
                    {selectedItem.avg_risk.toFixed(1)} / 100
                  </span>
                </div>
              </div>

              {/* Severity Breakdown */}
              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2.5">
                <span className="text-[10px] text-[#8A95AA] uppercase">
                  SEVERITY DISTRIBUTION
                </span>
                <div className="space-y-2 pt-1">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-[#FF4757]">CRITICAL</span>
                    <span className="text-[#E7ECF5] font-bold">
                      {selectedItem.critical_count}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-[#FF8A3D]">HIGH</span>
                    <span className="text-[#E7ECF5] font-bold">
                      {selectedItem.high_count}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="text-[#3FC7D4]">MEDIUM</span>
                    <span className="text-[#E7ECF5] font-bold">
                      {selectedItem.medium_count}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-[#8A95AA] font-mono text-xs py-12">
              Select a wedge to inspect threat class parameters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
