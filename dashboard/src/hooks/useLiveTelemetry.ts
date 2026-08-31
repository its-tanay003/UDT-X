import { useEffect, useRef, useState } from "react";
import type { Alert, Incident, PerformanceMetrics, WSMessage } from "../types/soc";

export function useLiveTelemetry(
  wsUrl: string = "ws://localhost:8000/ws/live",
  apiUrl: string = "http://localhost:8000"
) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    total_alerts: 0,
    total_incidents: 0,
    critical_alerts: 0,
    active_incidents: 0,
    average_risk_score: 28.4,
    flows_per_sec: 124850,
    alerts_per_min: 312,
    active_threats: 2,
    timestamp: new Date().toISOString(),
  });

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [perfRes, alertsRes, incsRes] = await Promise.allSettled([
          fetch(`${apiUrl}/performance`).then((r) => r.json()),
          fetch(`${apiUrl}/alerts?limit=15`).then((r) => r.json()),
          fetch(`${apiUrl}/incidents?limit=10`).then((r) => r.json()),
        ]);

        if (perfRes.status === "fulfilled" && perfRes.value) {
          setMetrics((prev) => ({
            ...prev,
            ...perfRes.value,
          }));
        }

        if (alertsRes.status === "fulfilled" && Array.isArray(alertsRes.value)) {
          setAlerts(alertsRes.value);
        }

        if (incsRes.status === "fulfilled" && Array.isArray(incsRes.value)) {
          setIncidents(incsRes.value);
        }
      } catch (err) {
        console.debug("Telemetry initial fetch:", err);
      }
    };

    fetchInitialData();
  }, [apiUrl]);

  useEffect(() => {
    let reconnectTimeout: any = null;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const parsed: WSMessage = JSON.parse(event.data);
            if (parsed.type === "NEW_ALERT" && parsed.data) {
              setAlerts((prev) => [parsed.data as Alert, ...prev].slice(0, 100));
            } else if (parsed.type === "NEW_INCIDENT" && parsed.data) {
              setIncidents((prev) => [parsed.data as Incident, ...prev].slice(0, 50));
            } else if (parsed.type === "METRICS_UPDATE" && parsed.data) {
              setMetrics((prev) => ({ ...prev, ...parsed.data }));
            }
          } catch (e) {
            console.debug("WS parse error:", e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (e) {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connect, 4000);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [wsUrl]);

  return { metrics, alerts, incidents, isConnected };
}
