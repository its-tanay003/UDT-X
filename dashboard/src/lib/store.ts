import { create } from "zustand";
import type { Alert, Incident, PerformanceMetrics, WSMessage } from "../types/soc";

interface LiveState {
  isConnected: boolean;
  isConnecting: boolean;
  hasLoadedInitial: boolean;
  lastPing: number;
  alerts: Alert[];
  incidents: Incident[];
  metrics: PerformanceMetrics | null;
  selectedAlertId: string | null;
  selectedIncidentId: string | null;

  // Actions
  setConnected: (connected: boolean) => void;
  addAlert: (alert: Alert) => void;
  setAlerts: (alerts: Alert[]) => void;
  addIncident: (incident: Incident) => void;
  setIncidents: (incidents: Incident[]) => void;
  updateMetrics: (partial: Partial<PerformanceMetrics>) => void;
  setSelectedAlert: (id: string | null) => void;
  setSelectedIncident: (id: string | null) => void;
  fetchInitialData: (apiUrl?: string) => Promise<void>;
  connectWebSocket: (url?: string, apiUrl?: string) => () => void;
}

export const useLiveStore = create<LiveState>((set, get) => ({
  isConnected: false,
  isConnecting: false,
  hasLoadedInitial: false,
  lastPing: Date.now(),
  alerts: [],
  incidents: [],
  metrics: null,
  selectedAlertId: null,
  selectedIncidentId: null,

  setConnected: (connected) => set({ isConnected: connected, isConnecting: false }),

  addAlert: (alert) =>
    set((state) => {
      const exists = state.alerts.some((a) => a.alert_id === alert.alert_id);
      if (exists) return state;
      const updated = [alert, ...state.alerts].slice(0, 500);
      return {
        alerts: updated,
        metrics: state.metrics
          ? {
              ...state.metrics,
              total_alerts: state.metrics.total_alerts + 1,
              critical_alerts:
                alert.severity === "critical"
                  ? state.metrics.critical_alerts + 1
                  : state.metrics.critical_alerts,
            }
          : null,
      };
    }),

  setAlerts: (alerts) => set({ alerts }),

  addIncident: (incident) =>
    set((state) => {
      const exists = state.incidents.some((i) => i.incident_id === incident.incident_id);
      if (exists) return state;
      return {
        incidents: [incident, ...state.incidents].slice(0, 100),
        metrics: state.metrics
          ? {
              ...state.metrics,
              total_incidents: state.metrics.total_incidents + 1,
              active_incidents: state.metrics.active_incidents + 1,
            }
          : null,
      };
    }),

  setIncidents: (incidents) => set({ incidents }),

  updateMetrics: (partial) =>
    set((state) => ({
      metrics: state.metrics ? { ...state.metrics, ...partial } : (partial as PerformanceMetrics),
    })),

  setSelectedAlert: (id) => set({ selectedAlertId: id }),
  setSelectedIncident: (id) => set({ selectedIncidentId: id }),

  fetchInitialData: async (apiUrl = "http://localhost:8000") => {
    try {
      const [perfRes, alertsRes, incsRes] = await Promise.allSettled([
        fetch(`${apiUrl}/performance`).then((r) => (r.ok ? r.json() : null)),
        fetch(`${apiUrl}/alerts?limit=15`).then((r) => (r.ok ? r.json() : [])),
        fetch(`${apiUrl}/incidents?limit=10`).then((r) => (r.ok ? r.json() : [])),
      ]);

      if (perfRes.status === "fulfilled" && perfRes.value) {
        set({ metrics: perfRes.value });
      }
      if (alertsRes.status === "fulfilled" && Array.isArray(alertsRes.value)) {
        set({ alerts: alertsRes.value });
      }
      if (incsRes.status === "fulfilled" && Array.isArray(incsRes.value)) {
        set({ incidents: incsRes.value });
      }
      set({ hasLoadedInitial: true });
    } catch (err) {
      console.debug("Initial REST telemetry fetch error:", err);
      set({ hasLoadedInitial: true });
    }
  },

  connectWebSocket: (url = "ws://localhost:8000/ws/live", apiUrl = "http://localhost:8000") => {
    // Kick off initial REST telemetry hydration once
    if (!get().hasLoadedInitial) {
      get().fetchInitialData(apiUrl);
    }

    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let isCleanedUp = false;

    const connect = () => {
      if (isCleanedUp) return;
      set({ isConnecting: true });

      try {
        ws = new WebSocket(url);

        ws.onopen = () => {
          if (isCleanedUp) {
            ws?.close();
            return;
          }
          set({ isConnected: true, isConnecting: false, lastPing: Date.now() });
        };

        ws.onmessage = (event) => {
          try {
            const parsed: WSMessage = JSON.parse(event.data);
            set({ lastPing: Date.now() });

            if (parsed.type === "NEW_ALERT" && parsed.data) {
              get().addAlert(parsed.data);
            } else if (parsed.type === "NEW_INCIDENT" && parsed.data) {
              get().addIncident(parsed.data);
            } else if (parsed.type === "METRICS_UPDATE" && parsed.data) {
              get().updateMetrics(parsed.data);
            }
          } catch (e) {
            console.debug("WS parse event error:", e);
          }
        };

        ws.onclose = () => {
          if (isCleanedUp) return;
          set({ isConnected: false, isConnecting: false });
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = (error) => {
          if (isCleanedUp) return;
          console.error("UDT-X Live WebSocket Handshake/Connection Error:", error);
          set({ isConnected: false, isConnecting: false });
        };
      } catch (err) {
        if (isCleanedUp) return;
        console.error("UDT-X WebSocket Initialization Error:", err);
        set({ isConnected: false, isConnecting: false });
        reconnectTimeout = setTimeout(connect, 4000);
      }
    };

    connect();

    return () => {
      isCleanedUp = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  },
}));
