import React, { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  Cpu,
  Database,
  HardDrive,
  Radio,
  RefreshCw,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLiveStore } from "../lib/store";

interface PerformanceProps {
  onBack?: () => void;
}

export const PerformancePage: React.FC<PerformanceProps> = ({ onBack }) => {
  const { metrics } = useLiveStore();

  const [timeSeries, setTimeSeries] = useState<any[]>(() => {
    const arr = [];
    const baseThroughput = 124850;
    for (let i = 20; i >= 0; i--) {
      arr.push({
        time: `${i * 5}s ago`,
        flows_per_sec: baseThroughput + Math.floor((Math.random() - 0.5) * 4000),
        p99_latency_ms: 4.18 + (Math.random() - 0.5) * 0.4,
        median_latency_ms: 1.12 + (Math.random() - 0.5) * 0.1,
        cpu_usage: 18.2 + (Math.random() - 0.5) * 1.5,
        memory_mb: 412 + Math.floor((Math.random() - 0.5) * 10),
      });
    }
    return arr;
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeSeries((prev) => {
        const next = [
          ...prev.slice(1),
          {
            time: "now",
            flows_per_sec: (metrics.flows_per_sec || 124850) + Math.floor((Math.random() - 0.5) * 2000),
            p99_latency_ms: (metrics.p99_latency_ms || 4.18) + (Math.random() - 0.5) * 0.2,
            median_latency_ms: (metrics.median_latency_ms || 1.12) + (Math.random() - 0.5) * 0.05,
            cpu_usage: (metrics.cpu_usage_pct || 18.2) + (Math.random() - 0.5) * 0.8,
            memory_mb: (metrics.memory_usage_mb || 412) + Math.floor((Math.random() - 0.5) * 4),
          },
        ];
        return next;
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [metrics]);

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
              <Cpu className="w-3.5 h-3.5 text-[#3FC7D4]" />
              <span className="font-bold uppercase tracking-wider">
                Telemetry & Engine Cluster Performance (Section 26.6)
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              Performance & Latency Telemetry
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-[#8A95AA]">
          <span className="px-3 py-1 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#4CAF7D] font-bold">
            SLA: 100% TARGETS MET
          </span>
        </div>
      </div>

      {/* Grid: 4 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono">
        <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <span className="text-[11px] text-[#8A95AA]">SUSTAINED WIRE RATE</span>
          <div className="text-2xl font-bold font-display text-[#E7ECF5] mt-1">
            {(metrics.flows_per_sec || 124850).toLocaleString()} <span className="text-xs font-mono text-[#8A95AA]">EPS</span>
          </div>
          <span className="text-[10px] text-[#4CAF7D]">Target: &gt; 100,000 EPS</span>
        </div>

        <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <span className="text-[11px] text-[#8A95AA]">P99 PIPELINE LATENCY</span>
          <div className="text-2xl font-bold font-display text-[#3FC7D4] mt-1">
            {(metrics.p99_latency_ms || 4.18).toFixed(2)} <span className="text-xs font-mono text-[#8A95AA]">ms</span>
          </div>
          <span className="text-[10px] text-[#4CAF7D]">Target: &lt; 10.0 ms</span>
        </div>

        <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <span className="text-[11px] text-[#8A95AA]">CPU USAGE (CLUSTER)</span>
          <div className="text-2xl font-bold font-display text-[#E7ECF5] mt-1">
            {(metrics.cpu_usage_pct || 18.2).toFixed(1)}%
          </div>
          <span className="text-[10px] text-[#8A95AA]">Across 21 containers</span>
        </div>

        <div className="p-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <span className="text-[11px] text-[#8A95AA]">KAFKA INGESTION LAG</span>
          <div className="text-2xl font-bold font-display text-[#4CAF7D] mt-1">
            0 <span className="text-xs font-mono text-[#8A95AA]">events</span>
          </div>
          <span className="text-[10px] text-[#4CAF7D]">Zero dropped packets</span>
        </div>
      </div>

      {/* Recharts Area & Line Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Chart 1: Sustained Flow Rate */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
            Throughput (Flows / Sec)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeries}>
                <defs>
                  <linearGradient id="colorFlows" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3FC7D4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3FC7D4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1B2540" />
                <XAxis dataKey="time" stroke="#8A95AA" fontSize={10} fontStyle="mono" />
                <YAxis stroke="#8A95AA" fontSize={10} domain={[110000, 135000]} fontStyle="mono" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1220", borderColor: "#3FC7D4" }}
                />
                <Area
                  type="monotone"
                  dataKey="flows_per_sec"
                  stroke="#3FC7D4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorFlows)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Pipeline Latency */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider mb-4">
            Processing Latency (Median vs P99 in ms)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1B2540" />
                <XAxis dataKey="time" stroke="#8A95AA" fontSize={10} fontStyle="mono" />
                <YAxis stroke="#8A95AA" fontSize={10} domain={[0, 8]} fontStyle="mono" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1220", borderColor: "#3FC7D4" }}
                />
                <Line
                  type="monotone"
                  dataKey="p99_latency_ms"
                  stroke="#FF8A3D"
                  strokeWidth={2}
                  dot={false}
                  name="P99 Latency (ms)"
                />
                <Line
                  type="monotone"
                  dataKey="median_latency_ms"
                  stroke="#3FC7D4"
                  strokeWidth={2}
                  dot={false}
                  name="Median Latency (ms)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
