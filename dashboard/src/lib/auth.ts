import { create } from "zustand";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "analyst" | "admin";
  avatar_seed: string;
  has_completed_tour: boolean;
  last_login_at?: string;
  created_at?: string;
}

export interface UserSettings {
  alerting: {
    sound_on_critical: boolean;
    min_notification_severity: "low" | "medium" | "high" | "critical";
    live_monitor_autoscroll: boolean;
  };
  display: {
    density: "comfortable" | "compact";
    sphere_particle_density: "high" | "low" | "off";
    default_time_range: "1h" | "24h" | "7d" | "30d";
  };
  data_export: {
    default_format: "CEF" | "Syslog" | "STIX";
  };
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  settings: UserSettings;
  isLoading: boolean;
  isThrottled: boolean;
  throttleSeconds: number;
  tourActive: boolean;
  tourStepIndex: number;

  // Actions
  setAuth: (user: User, token: string) => void;
  setToken: (token: string) => void;
  logout: () => Promise<void>;
  updateUser: (partial: Partial<User>) => void;
  setSettings: (settings: UserSettings) => void;
  updateSettingsField: <K extends keyof UserSettings>(
    category: K,
    fields: Partial<UserSettings[K]>
  ) => void;
  fetchSettings: () => Promise<void>;
  saveSettings: (newSettings: UserSettings) => Promise<void>;
  setThrottled: (seconds: number) => void;
  startTour: () => void;
  nextTourStep: () => void;
  prevTourStep: () => void;
  skipTour: () => Promise<void>;
  completeTour: () => Promise<void>;
}

const DEFAULT_SETTINGS: UserSettings = {
  alerting: {
    sound_on_critical: true,
    min_notification_severity: "high",
    live_monitor_autoscroll: true,
  },
  display: {
    density: "comfortable",
    sphere_particle_density: "high",
    default_time_range: "24h",
  },
  data_export: {
    default_format: "CEF",
  },
};

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  settings: DEFAULT_SETTINGS,
  isLoading: false,
  isThrottled: false,
  throttleSeconds: 0,
  tourActive: false,
  tourStepIndex: 0,

  setAuth: (user, token) => {
    set({ user, accessToken: token });
    get().fetchSettings();
    if (!user.has_completed_tour) {
      set({ tourActive: true, tourStepIndex: 0 });
    }
  },

  setToken: (token) => set({ accessToken: token }),

  logout: async () => {
    try {
      await fetch("http://localhost:8000/auth/logout", { method: "POST" });
    } catch (e) {
      console.debug("Logout cleanup error:", e);
    }
    set({ user: null, accessToken: null, tourActive: false });
  },

  updateUser: (partial) =>
    set((state) => ({
      user: state.user ? { ...state.user, ...partial } : null,
    })),

  setSettings: (settings) => set({ settings }),

  updateSettingsField: (category, fields) => {
    const updated = {
      ...get().settings,
      [category]: { ...get().settings[category], ...fields },
    };
    set({ settings: updated });
    get().saveSettings(updated);
  },

  fetchSettings: async () => {
    const token = get().accessToken;
    if (!token) return;
    try {
      const res = await fetch("http://localhost:8000/settings", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        set({ settings: data });
      }
    } catch (err) {
      console.debug("Failed to fetch settings from server:", err);
    }
  },

  saveSettings: async (newSettings) => {
    const token = get().accessToken;
    if (!token) return;
    try {
      await fetch("http://localhost:8000/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(newSettings),
      });
    } catch (err) {
      console.debug("Failed to persist settings:", err);
    }
  },

  setThrottled: (seconds) => {
    set({ isThrottled: true, throttleSeconds: seconds });
    const timer = setInterval(() => {
      const remaining = get().throttleSeconds - 1;
      if (remaining <= 0) {
        clearInterval(timer);
        set({ isThrottled: false, throttleSeconds: 0 });
      } else {
        set({ throttleSeconds: remaining });
      }
    }, 1000);
  },

  startTour: () => set({ tourActive: true, tourStepIndex: 0 }),
  nextTourStep: () => set((state) => ({ tourStepIndex: state.tourStepIndex + 1 })),
  prevTourStep: () =>
    set((state) => ({ tourStepIndex: Math.max(0, state.tourStepIndex - 1) })),

  skipTour: async () => {
    set({ tourActive: false });
    const token = get().accessToken;
    if (token) {
      try {
        await fetch("http://localhost:8000/auth/me", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ has_completed_tour: true }),
        });
        get().updateUser({ has_completed_tour: true });
      } catch (err) {
        console.debug("Error skipping tour:", err);
      }
    }
  },

  completeTour: async () => {
    set({ tourActive: false });
    const token = get().accessToken;
    if (token) {
      try {
        await fetch("http://localhost:8000/auth/me", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ has_completed_tour: true }),
        });
        get().updateUser({ has_completed_tour: true });
      } catch (err) {
        console.debug("Error completing tour:", err);
      }
    }
  },
}));

/**
 * Authenticated API Fetch client with 429 rate limit detection and 401 transparent token refresh.
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const authStore = useAuthStore.getState();
  const token = authStore.accessToken;

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response = await fetch(url, { ...options, headers });

  // Handle 429 Rate Limiting
  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get("Retry-After") || "10", 10);
    authStore.setThrottled(retryAfter);
    return response;
  }

  // Handle 401 Unauthorized token refresh
  if (response.status === 401) {
    try {
      const refreshRes = await fetch("http://localhost:8000/auth/refresh", {
        method: "POST",
      });
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        authStore.setToken(refreshData.access_token);
        headers.set("Authorization", `Bearer ${refreshData.access_token}`);
        response = await fetch(url, { ...options, headers });
      } else {
        authStore.logout();
      }
    } catch (e) {
      authStore.logout();
    }
  }

  return response;
}
