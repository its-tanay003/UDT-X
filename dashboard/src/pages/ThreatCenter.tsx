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
  HelpCircle,
} from "lucide-react";
import { fetchThreatStats, type ThreatStatsResponse, type ThreatStatItem } from "../lib/api/threats";
import { SonarRadialChart } from "../components/SonarRadialChart";
import { Tooltip } from "../components/Tooltip";

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

  const selectedItem: ThreatStatItem | undefined = stats?.classes.find(
    (c) => c.threat_class === selectedClass
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
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
              Threat Intelligence Center
            </h1>
            <p className="text-xs text-[#8A95AA] mt-0.5">
              Aggregated threat class intelligence, MITRE ATT&CK matrix mappings, and severity distributions.
            </p>
          </div>
        </div>

        {/* Time Filter Tabs */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs">
          {["1h", "24h", "7d", "30d"].map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-3 py-1.5 rounded transition-colors ${
                timeRange === r
                  ? "bg-[#3FC7D4]/20 text-[#3FC7D4] font-bold"
                  : "text-[#8A95AA] hover:text-[#E7ECF5]"
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Grid: Sonar Radial + Threat Breakdown Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Radial Sonar Distribution */}
        <div id="tour-threat-radar" className="lg:col-span-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
              <PieChart className="w-4 h-4 text-[#3FC7D4]" />
              <span className="font-bold uppercase tracking-wider text-[#E7ECF5]">
                Radial Sonar Threat Signature Matrix
              </span>
            </div>
            <Tooltip
              title="Sonar Radar"
              content="Radial multi-axis threat spectrum visualizing volume distribution across core attack classes."
            >
              <HelpCircle className="w-3.5 h-3.5 text-[#8A95AA] hover:text-[#3FC7D4] cursor-help" />
            </Tooltip>
          </div>

          <div className="flex-1 flex items-center justify-center min-h-75">
            {stats ? (
              <SonarRadialChart
                data={stats.classes}
                selectedClass={selectedClass}
                onSelectClass={(cat) => setSelectedClass(cat)}
              />
            ) : (
              <div className="font-mono text-xs text-[#8A95AA]">Loading Sonar data...</div>
            )}
          </div>
        </div>

        {/* Right Column: Selected Threat Profile Card */}
        <div className="lg:col-span-6 space-y-4">
          {selectedItem ? (
            <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs text-[#8A95AA] uppercase">
                    INSPECTING SIGNATURE
                  </span>
                  <h3 className="text-xl font-display font-bold text-[#E7ECF5]">
                    {selectedItem.threat_class}
                  </h3>
                </div>
                <div className="text-right font-mono">
                  <div className="text-xs text-[#8A95AA]">Total Occurrences</div>
                  <div className="text-xl font-bold text-[#3FC7D4]">
                    {selectedItem.count.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Severity Breakdown Meter */}
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between text-[#8A95AA]">
                  <span>Severity Distribution:</span>
                  <span>Avg Risk: {selectedItem.avg_risk.toFixed(1)}/100</span>
                </div>
                <div className="w-full h-3 rounded-full bg-[#0B1220] overflow-hidden flex">
                  <div
                    className="bg-[#FF4757] h-full"
                    style={{
                      width: `${(selectedItem.critical_count / selectedItem.count) * 100}%`,
                    }}
                    title={`Critical: ${selectedItem.critical_count}`}
                  />
                  <div
                    className="bg-[#FF8A3D] h-full"
                    style={{
                      width: `${(selectedItem.high_count / selectedItem.count) * 100}%`,
                    }}
                    title={`High: ${selectedItem.high_count}`}
                  />
                  <div
                    className="bg-[#EAB308] h-full"
                    style={{
                      width: `${(selectedItem.medium_count / selectedItem.count) * 100}%`,
                    }}
                    title={`Medium: ${selectedItem.medium_count}`}
                  />
                  <div
                    className="bg-[#4CAF7D] h-full"
                    style={{
                      width: `${(selectedItem.low_count / selectedItem.count) * 100}%`,
                    }}
                    title={`Low: ${selectedItem.low_count}`}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-[#8A95AA] pt-1">
                  <span className="text-[#FF4757]">
                    ● Crit ({selectedItem.critical_count})
                  </span>
                  <span className="text-[#FF8A3D]">
                    ● High ({selectedItem.high_count})
                  </span>
                  <span className="text-[#EAB308]">
                    ● Med ({selectedItem.medium_count})
                  </span>
                  <span className="text-[#4CAF7D]">
                    ● Low ({selectedItem.low_count})
                  </span>
                </div>
              </div>

              {/* Engine Strategy & Heuristic Rules */}
              <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2 font-mono text-xs">
                <span className="text-[#8A95AA] uppercase text-[10px]">
                  Detection Strategy & Baseline Parameters:
                </span>
                <p className="text-xs text-[#E7ECF5] leading-relaxed">
                  Evaluated using passive real-time flow feature extraction. Compares packet periodicity, entropy variance, and flag asymmetry against a baseline Gaussian profile with sub-millisecond scoring.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 text-center font-mono text-xs text-[#8A95AA]">
              Select a threat class from the Sonar radar to inspect detailed metrics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
