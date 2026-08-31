import React from "react";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color: "cyan" | "rose" | "amber" | "emerald" | "violet";
  trend?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
}) => {
  const colorMap = {
    cyan: {
      bg: "from-cyan-500/10 to-blue-500/5",
      border: "border-cyan-500/30",
      iconBg: "bg-cyan-500/20 text-cyan-400 border-cyan-500/40",
      glow: "group-hover:shadow-cyan-500/10",
      valColor: "text-cyan-100",
    },
    rose: {
      bg: "from-rose-500/10 to-red-500/5",
      border: "border-rose-500/30",
      iconBg: "bg-rose-500/20 text-rose-400 border-rose-500/40",
      glow: "group-hover:shadow-rose-500/10",
      valColor: "text-rose-100",
    },
    amber: {
      bg: "from-amber-500/10 to-orange-500/5",
      border: "border-amber-500/30",
      iconBg: "bg-amber-500/20 text-amber-400 border-amber-500/40",
      glow: "group-hover:shadow-amber-500/10",
      valColor: "text-amber-100",
    },
    emerald: {
      bg: "from-emerald-500/10 to-teal-500/5",
      border: "border-emerald-500/30",
      iconBg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
      glow: "group-hover:shadow-emerald-500/10",
      valColor: "text-emerald-100",
    },
    violet: {
      bg: "from-violet-500/10 to-purple-500/5",
      border: "border-violet-500/30",
      iconBg: "bg-violet-500/20 text-violet-400 border-violet-500/40",
      glow: "group-hover:shadow-violet-500/10",
      valColor: "text-violet-100",
    },
  };

  const scheme = colorMap[color];

  return (
    <div
      className={`group relative overflow-hidden p-6 rounded-2xl bg-gradient-to-br ${scheme.bg} border ${scheme.border} backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${scheme.glow}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
            {title}
          </p>
          <h3 className={`mt-2 text-3xl font-black font-mono tracking-tight ${scheme.valColor}`}>
            {value}
          </h3>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400 flex items-center gap-1">
              {subtitle}
            </p>
          )}
          {trend && (
            <span className="inline-block mt-2 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              {trend}
            </span>
          )}
        </div>

        <div className={`p-3.5 rounded-xl border ${scheme.iconBg} shadow-inner`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};
