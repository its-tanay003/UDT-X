import React from "react";

interface RiskGaugeProps {
  score: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score }) => {
  const safeScore = Math.max(0, Math.min(100, score || 0));

  // Determine color and status badge
  let strokeColor = "#10b981"; // Low / Emerald
  let statusText = "NOMINAL / LOW RISK";
  let statusBg = "rgba(16, 185, 129, 0.15)";
  let statusColor = "#34d399";

  if (safeScore >= 80) {
    strokeColor = "#ef4444"; // Critical / Red
    statusText = "CRITICAL THREAT POSTURE";
    statusBg = "rgba(239, 68, 68, 0.15)";
    statusColor = "#f87171";
  } else if (safeScore >= 60) {
    strokeColor = "#f97316"; // High / Orange
    statusText = "HIGH ALERT / ACTIVE INCIDENTS";
    statusBg = "rgba(249, 115, 22, 0.15)";
    statusColor = "#fb923c";
  } else if (safeScore >= 35) {
    strokeColor = "#eab308"; // Medium / Amber
    statusText = "ELEVATED POSTURE";
    statusBg = "rgba(234, 179, 8, 0.15)";
    statusColor = "#fde047";
  }

  // Semi-circle gauge math
  const radius = 70;
  const strokeWidth = 14;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (safeScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-slate-900/90 border border-slate-800/80 rounded-2xl backdrop-blur-xl shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="text-xs font-semibold tracking-wider text-slate-400 uppercase mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        Global Risk Posture
      </div>

      <div className="relative w-48 h-28 flex items-center justify-center">
        <svg className="w-48 h-48 transform -rotate-180" viewBox="0 0 180 180">
          {/* Background Arc */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="transparent"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset="0"
            strokeLinecap="round"
          />
          {/* Active Value Arc */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: "stroke-dashoffset 0.8s ease-in-out, stroke 0.5s ease",
              filter: `drop-shadow(0 0 8px ${strokeColor}66)`,
            }}
          />
        </svg>

        {/* Value in Center */}
        <div className="absolute top-12 flex flex-col items-center">
          <span className="text-4xl font-extrabold tracking-tight text-white font-mono">
            {safeScore.toFixed(1)}
          </span>
          <span className="text-[10px] text-slate-400 font-medium tracking-widest uppercase">
            Score / 100
          </span>
        </div>
      </div>

      {/* Posture Badge */}
      <div
        className="mt-2 px-3 py-1 rounded-full text-xs font-bold tracking-wide flex items-center gap-1.5 border"
        style={{
          backgroundColor: statusBg,
          color: statusColor,
          borderColor: `${statusColor}40`,
        }}
      >
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: statusColor }}
        />
        {statusText}
      </div>
    </div>
  );
};
