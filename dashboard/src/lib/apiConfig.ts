/**
 * Dynamic API and WebSocket endpoint resolver for UDT-X.
 * Automatically synchronizes with the browser's hostname (e.g., localhost, 127.0.0.1, or remote LAN IP)
 * to avoid CORS / hostname mismatch rejections.
 */

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }
  const hostname = window.location.hostname;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return `http://${hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

export function getWebSocketBaseUrl(): string {
  if (typeof window === "undefined") {
    return "ws://127.0.0.1:8000";
  }
  const hostname = window.location.hostname;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return `${protocol}//${hostname}:8000`;
  }
  return `${protocol}//127.0.0.1:8000`;
}
