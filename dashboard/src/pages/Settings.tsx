import React, { useState, useEffect } from "react";
import { Settings, Bell, Monitor, Database, Shield, CheckCircle } from "lucide-react";
import { useAuthStore } from "../lib/auth";

export const SettingsPage: React.FC = () => {
  const { user, settings, updateSettingsField } = useAuthStore();
  const [stationConfig, setStationConfig] = useState<any>(null);
  const [savedToast, setSavedToast] = useState(false);

  useEffect(() => {
    if (user?.role === "admin") {
      fetch("http://localhost:8000/settings/station-config", {
        headers: { Authorization: `Bearer ${useAuthStore.getState().accessToken}` },
      })
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => setStationConfig(data))
        .catch(() => {});
    }
  }, [user]);

  const triggerSaveNotification = () => {
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Station Telemetry & Interface Preferences
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Station Settings
          </h1>
        </div>

        {savedToast && (
          <div className="flex items-center gap-2 font-mono text-xs text-[#4CAF7D] bg-[#4CAF7D]/15 border border-[#4CAF7D]/30 px-3 py-1.5 rounded-lg animate-fade-in">
            <CheckCircle className="w-4 h-4" />
            <span>PREFERENCES PERSISTED TO STATION DB</span>
          </div>
        )}
      </div>

      {/* Grid: 3 Main Preference Panels */}
      <div id="tour-settings-panel" className="grid grid-cols-1 lg:grid-cols-2 gap-5 font-mono text-xs">
        {/* Panel 1: Alerting & Audio */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
          <h3 className="text-xs font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
            <Bell className="w-4 h-4 text-[#3FC7D4]" />
            Alerting & Notification Rules
          </h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
              <div>
                <div className="font-bold text-[#E7ECF5]">Audio Ping on Critical Threat</div>
                <div className="text-[10px] text-[#8A95AA]">Emit audio pulse when critical alerts appear</div>
              </div>
              <input
                type="checkbox"
                checked={settings.alerting.sound_on_critical}
                onChange={(e) => {
                  updateSettingsField("alerting", { sound_on_critical: e.target.checked });
                  triggerSaveNotification();
                }}
                className="w-4 h-4 accent-[#3FC7D4] cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
              <div>
                <div className="font-bold text-[#E7ECF5]">Live Monitor Auto-Scroll</div>
                <div className="text-[10px] text-[#8A95AA]">Automatically pin feed to newest telemetry packet</div>
              </div>
              <input
                type="checkbox"
                checked={settings.alerting.live_monitor_autoscroll}
                onChange={(e) => {
                  updateSettingsField("alerting", { live_monitor_autoscroll: e.target.checked });
                  triggerSaveNotification();
                }}
                className="w-4 h-4 accent-[#3FC7D4] cursor-pointer"
              />
            </div>

            <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 space-y-2">
              <div className="font-bold text-[#E7ECF5]">Minimum Notification Threshold</div>
              <select
                value={settings.alerting.min_notification_severity}
                onChange={(e) => {
                  updateSettingsField("alerting", {
                    min_notification_severity: e.target.value as any,
                  });
                  triggerSaveNotification();
                }}
                className="w-full px-3 py-1.5 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
              >
                <option value="low">LOW (All Events)</option>
                <option value="medium">MEDIUM (Suspicious + Critical)</option>
                <option value="high">HIGH (Severe + Critical)</option>
                <option value="critical">CRITICAL ONLY</option>
              </select>
            </div>
          </div>
        </div>

        {/* Panel 2: Display & 3D Listening Sphere */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
          <h3 className="text-xs font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
            <Monitor className="w-4 h-4 text-[#FF8A3D]" />
            Display & Visual Instrumentation
          </h3>

          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 space-y-2">
              <div className="font-bold text-[#E7ECF5]">3D Listening Sphere Particle Density</div>
              <div className="text-[10px] text-[#8A95AA]">
                Control particle workload for low-power hardware
              </div>
              <select
                value={settings.display.sphere_particle_density}
                onChange={(e) => {
                  updateSettingsField("display", {
                    sphere_particle_density: e.target.value as any,
                  });
                  triggerSaveNotification();
                }}
                className="w-full px-3 py-1.5 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
              >
                <option value="high">HIGH DENSITY (Full Visual Arcs)</option>
                <option value="low">LOW DENSITY (Reduced GPU Overhead)</option>
                <option value="off">OFF (Static Accessible Perimeter Ring)</option>
              </select>
            </div>

            <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 space-y-2">
              <div className="font-bold text-[#E7ECF5]">Default Analytics Time Range</div>
              <select
                value={settings.display.default_time_range}
                onChange={(e) => {
                  updateSettingsField("display", {
                    default_time_range: e.target.value as any,
                  });
                  triggerSaveNotification();
                }}
                className="w-full px-3 py-1.5 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
              >
                <option value="1h">1 Hour (Tactical)</option>
                <option value="24h">24 Hours (Standard Shift)</option>
                <option value="7d">7 Days (Weekly Model Baseline)</option>
                <option value="30d">30 Days (Monthly Trend)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Panel 3: Data & SIEM Export Defaults */}
        <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
          <h3 className="text-xs font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-[#4CAF7D]" />
            SIEM Interoperability & Export Format
          </h3>

          <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 space-y-2">
            <div className="font-bold text-[#E7ECF5]">Default Alert Export Format</div>
            <select
              value={settings.data_export.default_format}
              onChange={(e) => {
                updateSettingsField("data_export", {
                  default_format: e.target.value as any,
                });
                triggerSaveNotification();
              }}
              className="w-full px-3 py-1.5 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
            >
              <option value="CEF">Common Event Format (ArcSight / Splunk)</option>
              <option value="Syslog">Syslog RFC 5424 Format</option>
              <option value="STIX">STIX / TAXII v2.1 JSON Format</option>
            </select>
          </div>
        </div>

        {/* Panel 4: Station Configuration (Admin Read-Only) */}
        {user?.role === "admin" && stationConfig && (
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/25 space-y-4">
            <h3 className="text-xs font-bold text-[#3FC7D4] uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Operational Station Hardware Configuration
            </h3>

            <div className="space-y-2 p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Pipeline Version:</span>
                <span className="text-[#E7ECF5]">{stationConfig.pipeline_version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Enclave Mode:</span>
                <span className="text-[#3FC7D4]">{stationConfig.enclave_mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Rate Limiter Backend:</span>
                <span className="text-[#4CAF7D]">{stationConfig.rate_limiting_backend}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">JWT Token Expiry:</span>
                <span className="text-[#E7ECF5]">{stationConfig.jwt_expiry_minutes} mins</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
