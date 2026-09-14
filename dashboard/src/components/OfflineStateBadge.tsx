import React from "react";
import { WifiOff, AlertTriangle } from "lucide-react";
import { useLiveStore } from "../lib/store";

interface Props {
  variant?: "banner" | "badge";
  className?: string;
}

export const OfflineStateBadge: React.FC<Props> = ({ variant = "badge", className = "" }) => {
  const isOffline = useLiveStore((s) => s.isOffline);
  const isOfflineFallback = useLiveStore((s) => s.isOfflineFallback);
  const isConnected = useLiveStore((s) => s.isConnected);
  const lastTelemetryTimestamp = useLiveStore((s) => s.lastTelemetryTimestamp);

  // Active if explicitly offline, served from fallback cache, or disconnected with cached data
  const shouldShow = isOffline || isOfflineFallback || (!isConnected && lastTelemetryTimestamp !== null);

  if (!shouldShow) return null;

  if (variant === "banner") {
    return (
      <div
        className={`w-full py-2 px-4 rounded-xl bg-[#FF8A3D]/15 border border-[#FF8A3D]/40 flex items-center justify-between gap-3 text-xs font-mono text-[#FF8A3D] shadow-[0_0_15px_rgba(255,138,61,0.15)] ${className}`}
        role="alert"
      >
        <div className="flex items-center gap-2">
          <WifiOff className="w-4 h-4 shrink-0 animate-pulse text-[#FF8A3D]" />
          <span className="font-bold tracking-wider">LAST KNOWN STATE — OFFLINE</span>
          <span className="hidden sm:inline text-[#FF8A3D]/80">
            • Live telemetry stream paused. Displaying cached enclave state.
          </span>
        </div>
        {lastTelemetryTimestamp && (
          <span className="text-[10px] text-[#FF8A3D]/70 shrink-0">
            Cached: {new Date(lastTelemetryTimestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#FF8A3D]/15 border border-[#FF8A3D]/40 text-[11px] font-mono font-bold tracking-wider text-[#FF8A3D] shadow-[0_0_10px_rgba(255,138,61,0.2)] ${className}`}
      title="Network disconnected. Telemetry is served from local fallback cache."
    >
      <AlertTriangle className="w-3.5 h-3.5 shrink-0 animate-pulse text-[#FF8A3D]" />
      <span>LAST KNOWN STATE — OFFLINE</span>
    </div>
  );
};
