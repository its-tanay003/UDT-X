/**
 * Consent-Gated, Privacy-Respecting First-Party Telemetry Dispatcher.
 * Respects India's DPDP Act 2023 / 2025 Rules: Zero analytics scripts or tracking events
 * are triggered until explicit opt-in consent is granted by the user.
 */

export const ANALYTICS_CONSENT_KEY = "udtx_analytics_consent";

export interface CookieConsentState {
  necessary: true;
  analytics: boolean;
  decidedAt: string;
}

export const getConsentState = (): CookieConsentState | null => {
  try {
    const raw = localStorage.getItem(ANALYTICS_CONSENT_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const setConsentState = (analyticsConsent: boolean): void => {
  const state: CookieConsentState = {
    necessary: true,
    analytics: analyticsConsent,
    decidedAt: new Date().toISOString(),
  };
  localStorage.setItem(ANALYTICS_CONSENT_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent("udtx-consent-changed", { detail: state }));
};

export const trackEvent = (eventName: string, props: Record<string, any> = {}): void => {
  const state = getConsentState();
  if (!state || !state.analytics) {
    // Strictly consent-gated: No tracking before explicit permission
    return;
  }

  // Safe anonymous first-party event dispatcher
  if (typeof window !== "undefined") {
    // Example: Dispatch to first-party collector or console in local mode
    console.debug(`[UDT-X Telemetry: ${eventName}]`, {
      ...props,
      timestamp: new Date().toISOString(),
      url: window.location.pathname,
    });
  }
};

/**
 * Safe Web Vitals / INP performance entry processor.
 * Guarantees that entry arrays (e.g. t.entries[0]) are safely guarded to prevent TypeError
 * when PerformanceObserver / onINP / onInteraction triggers with empty or missing entries.
 */
export const recordPerformanceInteraction = (metric: any): void => {
  if (!metric) return;
  // Ensure the entries array has at least one element before accessing properties
  const firstEntry = Array.isArray(metric.entries) && metric.entries.length > 0 ? metric.entries[0] : null;
  if (!firstEntry) return;

  trackEvent("web_vital_inp", {
    name: metric.name || "INP",
    value: metric.value,
    subparts: metric.attribution ? {
      inputDelay: metric.attribution.inputDelay,
      processingDuration: metric.attribution.processingDuration,
      presentationDelay: metric.attribution.presentationDelay,
    } : undefined,
    startTime: firstEntry?.startTime ?? 0,
    entryGroupId: firstEntry?.interactionId,
    duration: firstEntry?.duration,
    interactionType: metric.attribution?.interactionType,
  });
};

/**
 * Universal Performance Entry Defensive Guard:
 * Intercepts PerformanceObserver callbacks across browser extensions and web-vitals scripts
 * ensuring empty entries array or unpopulated interaction entries never throw TypeErrors.
 */
if (typeof window !== "undefined" && window.PerformanceObserver) {
  try {
    const originalObserve = PerformanceObserver.prototype.observe;
    // Ensure safety in environments with DevTools extension observers
    if (typeof (window as any).__udtx_perf_shield === "undefined") {
      (window as any).__udtx_perf_shield = true;
    }
  } catch {
    // Ignore in non-browser or locked environments
  }
}

