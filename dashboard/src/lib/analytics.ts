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
