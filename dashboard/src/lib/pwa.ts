/**
 * UDT-X Progressive Web App & Service Worker Management
 *
 * Handles:
 * - Service worker registration and update detection
 * - User-prompted app-shell updates (no silent replacement)
 * - Storage quota estimation via navigator.storage.estimate()
 */

import { Workbox } from "workbox-window";

export interface StorageQuotaInfo {
  usage: number; // in bytes
  quota: number; // in bytes
  usagePercent: number;
  usageMB: string;
  quotaMB: string;
  isNearQuota: boolean;
}

type UpdateCallback = () => void;
let updateListener: UpdateCallback | null = null;
let wbInstance: Workbox | null = null;

export function registerServiceWorker(onUpdateAvailable?: () => void) {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
    return;
  }

  if (onUpdateAvailable) {
    updateListener = onUpdateAvailable;
  }

  try {
    wbInstance = new Workbox("/sw.js");

    wbInstance.addEventListener("waiting", () => {
      console.log("[UDT-X PWA] New service worker version waiting to activate");
      if (updateListener) {
        updateListener();
      }
    });

    wbInstance.addEventListener("controlling", () => {
      console.log("[UDT-X PWA] Service worker controlling page. Reloading...");
      window.location.reload();
    });

    wbInstance.register().catch((err) => {
      console.warn("[UDT-X PWA] Service worker registration failed:", err);
    });
  } catch (err) {
    console.debug("[UDT-X PWA] Workbox initialization note:", err);
    // Fallback to standard navigator registration
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => {
        reg.addEventListener("updatefound", () => {
          const newWorker = reg.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
                if (updateListener) updateListener();
              }
            });
          }
        });
      })
      .catch(() => {});
  }
}

export function activateWaitingUpdate() {
  if (wbInstance) {
    wbInstance.messageSkipWaiting();
  } else if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.ready.then((reg) => {
      if (reg.waiting) {
        reg.waiting.postMessage({ type: "SKIP_WAITING" });
      }
    });
  }
}

/**
 * Storage Quota Estimation (Section 5)
 * Checks browser storage utilization and detects when quota is getting full (>80%).
 */
export async function getStorageQuota(): Promise<StorageQuotaInfo> {
  if (typeof navigator !== "undefined" && navigator.storage && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate();
      const usage = estimate.usage || 0;
      const quota = estimate.quota || 1024 * 1024 * 1024; // Default 1GB fallback
      const usagePercent = quota > 0 ? (usage / quota) * 100 : 0;

      return {
        usage,
        quota,
        usagePercent: parseFloat(usagePercent.toFixed(1)),
        usageMB: (usage / (1024 * 1024)).toFixed(2),
        quotaMB: (quota / (1024 * 1024)).toFixed(0),
        isNearQuota: usagePercent > 80,
      };
    } catch (e) {
      console.debug("[UDT-X PWA] Storage estimate unavailable:", e);
    }
  }

  return {
    usage: 0,
    quota: 1024 * 1024 * 500,
    usagePercent: 0,
    usageMB: "0.00",
    quotaMB: "500",
    isNearQuota: false,
  };
}

/**
 * Proactively prune runtime cache if quota exceeds safe margins
 */
export async function pruneRuntimeCacheIfNeeded() {
  const quotaInfo = await getStorageQuota();
  if (quotaInfo.isNearQuota && "caches" in window) {
    console.warn("[UDT-X PWA] High storage usage detected. Trimming security fallback cache...");
    try {
      const cache = await caches.open("udtx-security-fallback-udtx-v1");
      const keys = await cache.keys();
      if (keys.length > 10) {
        // Evict half of cache
        const toDelete = keys.slice(0, Math.floor(keys.length / 2));
        for (const req of toDelete) {
          await cache.delete(req);
        }
      }
    } catch (e) {
      console.debug("[UDT-X PWA] Cache trim error:", e);
    }
  }
}
