import React, { useState } from "react";
import { Shield, Key, AlertTriangle, ArrowRight, Radio } from "lucide-react";
import { useAuthStore } from "../lib/auth";

interface LoginProps {
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginProps> = ({ onSuccess }) => {
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState("admin@udtx.local");
  const [password, setPassword] = useState("AdminEnclave2026!");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Authentication to enclave rejected");
      }

      const data = await res.json();
      setAuth(data.user, data.access_token);
      onSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to authenticate station");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-screen h-screen bg-[#0B1220] flex items-center justify-center p-6 relative select-none">
      {/* Background Ambience / Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(63,199,212,0.06)_0%,transparent_70%)] pointer-events-none" />

      <div className="w-full max-w-md p-8 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/25 shadow-2xl relative z-10 space-y-6">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(63,199,212,0.2)]">
            <Shield className="w-6 h-6 text-[#3FC7D4]" />
          </div>
          <div className="text-[10px] font-mono tracking-widest text-[#3FC7D4] uppercase">
            Restricted Enclave Console
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] tracking-tight">
            AUTHENTICATE TO STATION
          </h1>
          <p className="text-xs font-mono text-[#8A95AA]">
            Data-Diode Passive Network Defense Enclave
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3.5 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/40 flex items-center gap-2.5 font-mono text-xs text-[#FF4757]">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 font-mono text-xs">
          <div className="space-y-1.5">
            <label className="text-[#8A95AA] uppercase tracking-wider text-[10px]">
              Analyst Enclave Email / Call-Sign
            </label>
            <input
              type="text"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@udtx.local"
              className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] placeholder-[#8A95AA]/50 focus:outline-none focus:border-[#3FC7D4]"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[#8A95AA] uppercase tracking-wider text-[10px]">
              Station Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3.5 py-2.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] placeholder-[#8A95AA]/50 focus:outline-none focus:border-[#3FC7D4]"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-lg bg-[#3FC7D4] hover:bg-[#35B2BE] text-[#0B1220] font-bold text-xs uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(63,199,212,0.3)] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <span>INITIALIZING ACCESS...</span>
              ) : (
                <>
                  <span>INITIALIZE STATION ACCESS</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Demo Credentials Helper */}
        <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 font-mono text-[11px] text-[#8A95AA] space-y-1">
          <div className="flex justify-between text-[#3FC7D4]">
            <span>ADMIN ACCOUNT:</span>
            <span>admin@udtx.local</span>
          </div>
          <div className="flex justify-between">
            <span>PASSWORD:</span>
            <span className="text-[#E7ECF5]">AdminEnclave2026!</span>
          </div>
        </div>
      </div>
    </div>
  );
};
