import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield, Key, AlertTriangle, ArrowRight, ArrowLeft } from "lucide-react";
import { useAuthStore } from "../lib/auth";
import { SEO } from "../components/SEO";

import { getApiBaseUrl } from "../lib/apiConfig";

interface LoginProps {
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginProps> = ({ onSuccess }) => {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@udtx.local");
  const [password, setPassword] = useState("AdminEnclave2026!");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const apiHost = getApiBaseUrl();

      const res = await fetch(`${apiHost}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Authentication to enclave rejected. Please check email/password.");
      }

      const data = await res.json();
      setAuth(data.user, data.access_token);
      onSuccess();
      navigate("/app", { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to authenticate station. Ensure backend is online on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (accEmail: string, accPass: string) => {
    setEmail(accEmail);
    setPassword(accPass);
    setErrorMessage(null);
  };

  return (
    <div className="w-screen min-h-screen bg-[#0B1220] flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8 relative select-none">
      <SEO
        title="Station Login | Restricted Enclave Console — UDT-X"
        description="Authenticate to the UDT-X Autonomous Network Defense Enclave. Hardware-guarded passive optical SIGINT listening post."
        canonical="https://udtx.security/login"
      />

      {/* Background Ambience / Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(63,199,212,0.06)_0%,transparent_70%)] pointer-events-none" />

      {/* Top Bar Link back to Public Home */}
      <div className="absolute top-4 left-4 sm:left-8 z-20">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-xs font-mono text-[#8A95AA] hover:text-[#3FC7D4] transition-colors p-2 rounded-lg bg-[#131B2E]/60 border border-[#3FC7D4]/15 backdrop-blur-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Public Home</span>
        </Link>
      </div>

      <div className="w-full max-w-md my-auto p-6 sm:p-8 rounded-2xl bg-[#131B2E] border border-[#3FC7D4]/25 shadow-2xl relative z-10 space-y-6">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(63,199,212,0.2)]">
            <Shield className="w-6 h-6 text-[#3FC7D4]" />
          </div>
          <div className="text-[10px] font-mono tracking-widest text-[#3FC7D4] uppercase">
            Restricted Enclave Console
          </div>
          <h1 className="text-xl sm:text-2xl font-display font-bold text-[#E7ECF5] tracking-tight">
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
              type="email"
              required
              autoComplete="username"
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
              autoComplete="current-password"
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
        <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 font-mono text-[11px] text-[#8A95AA] space-y-2.5">
          <div className="text-[10px] uppercase text-[#8A95AA] tracking-wider font-bold">
            Demo Enclave Accounts (Click to Fill):
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill("admin@udtx.local", "AdminEnclave2026!")}
              className="p-2 rounded bg-[#131B2E] border border-[#3FC7D4]/30 hover:border-[#3FC7D4] text-left transition-colors"
            >
              <div className="text-[#3FC7D4] font-bold text-[10px]">👑 ADMINISTRATOR</div>
              <div className="text-[9px] text-[#E7ECF5] truncate">admin@udtx.local</div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("analyst@udtx.local", "AnalystEnclave2026!")}
              className="p-2 rounded bg-[#131B2E] border border-[#4CAF7D]/30 hover:border-[#4CAF7D] text-left transition-colors"
            >
              <div className="text-[#4CAF7D] font-bold text-[10px]">🛡️ ANALYST LEAD</div>
              <div className="text-[9px] text-[#E7ECF5] truncate">analyst@udtx.local</div>
            </button>
          </div>
        </div>

        {/* Compliance Links Footer */}
        <div className="pt-2 text-center font-mono text-[10px] text-[#8A95AA] flex items-center justify-center gap-3">
          <Link to="/privacy" className="hover:text-[#3FC7D4] underline">
            Privacy (DPDP)
          </Link>
          <span>•</span>
          <Link to="/terms" className="hover:text-[#3FC7D4] underline">
            Terms of Use
          </Link>
          <span>•</span>
          <Link to="/faq" className="hover:text-[#3FC7D4] underline">
            FAQ
          </Link>
        </div>
      </div>
    </div>
  );
};
