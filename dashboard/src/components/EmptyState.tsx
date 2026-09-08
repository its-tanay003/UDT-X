import React from "react";
import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { ShieldAlert } from "lucide-react";

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionTo?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  secondaryActionTo?: string;
  variant?: "default" | "warn" | "critical" | "signal";
  compact?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = ShieldAlert,
  title,
  description,
  actionLabel,
  actionTo,
  onAction,
  secondaryActionLabel,
  secondaryActionTo,
  variant = "default",
  compact = false,
}) => {
  const variantStyles = {
    default: {
      iconColor: "text-[#3FC7D4]",
      iconBg: "bg-[#3FC7D4]/10 border-[#3FC7D4]/30",
      glow: "shadow-[0_0_20px_rgba(63,199,212,0.1)]",
      btnClass: "bg-[#3FC7D4]/15 border-[#3FC7D4]/40 text-[#3FC7D4] hover:bg-[#3FC7D4]/25 hover:border-[#3FC7D4]/60",
    },
    signal: {
      iconColor: "text-[#3FC7D4]",
      iconBg: "bg-[#3FC7D4]/15 border-[#3FC7D4]/40",
      glow: "shadow-[0_0_25px_rgba(63,199,212,0.15)]",
      btnClass: "bg-[#3FC7D4]/20 border-[#3FC7D4]/50 text-[#3FC7D4] hover:bg-[#3FC7D4]/30",
    },
    warn: {
      iconColor: "text-[#FF8A3D]",
      iconBg: "bg-[#FF8A3D]/10 border-[#FF8A3D]/30",
      glow: "shadow-[0_0_20px_rgba(255,138,61,0.1)]",
      btnClass: "bg-[#FF8A3D]/15 border-[#FF8A3D]/40 text-[#FF8A3D] hover:bg-[#FF8A3D]/25",
    },
    critical: {
      iconColor: "text-[#FF4757]",
      iconBg: "bg-[#FF4757]/10 border-[#FF4757]/30",
      glow: "shadow-[0_0_20px_rgba(255,71,87,0.1)]",
      btnClass: "bg-[#FF4757]/15 border-[#FF4757]/40 text-[#FF4757] hover:bg-[#FF4757]/25",
    },
  }[variant];

  return (
    <div
      className={`rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 text-center flex flex-col items-center justify-center transition-all ${
        compact ? "p-6 space-y-3" : "p-12 space-y-4"
      } ${variantStyles.glow}`}
    >
      <div
        className={`rounded-2xl border p-3.5 flex items-center justify-center ${variantStyles.iconBg}`}
      >
        <Icon className={`${compact ? "w-6 h-6" : "w-8 h-8"} ${variantStyles.iconColor}`} />
      </div>

      <div className="space-y-1.5 max-w-md">
        <h3 className="text-sm font-display font-bold uppercase tracking-wider text-[#E7ECF5]">
          {title}
        </h3>
        <p className="text-xs text-[#8A95AA] leading-relaxed">
          {description}
        </p>
      </div>

      {(actionLabel || secondaryActionLabel) && (
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          {actionLabel && (
            actionTo ? (
              <Link
                to={actionTo}
                className={`px-4 py-2 rounded-lg border text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${variantStyles.btnClass}`}
              >
                <span>{actionLabel}</span>
              </Link>
            ) : (
              <button
                type="button"
                onClick={onAction}
                className={`px-4 py-2 rounded-lg border text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${variantStyles.btnClass}`}
              >
                <span>{actionLabel}</span>
              </button>
            )
          )}

          {secondaryActionLabel && secondaryActionTo && (
            <Link
              to={secondaryActionTo}
              className="px-3.5 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] text-xs font-mono transition-colors"
            >
              {secondaryActionLabel}
            </Link>
          )}
        </div>
      )}
    </div>
  );
};
