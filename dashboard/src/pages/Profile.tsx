import React, { useState, useEffect } from "react";
import { User, Shield, Key, UserCheck, AlertTriangle, CheckCircle, Plus } from "lucide-react";
import { useAuthStore } from "../lib/auth";

export const ProfilePage: React.FC = () => {
  const { user, updateUser, logout } = useAuthStore();
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [usersList, setUsersList] = useState<any[]>([]);

  // Admin provisioning state
  const [provEmail, setProvEmail] = useState("");
  const [provName, setProvName] = useState("");
  const [provPassword, setProvPassword] = useState("");
  const [provRole, setProvRole] = useState("analyst");

  useEffect(() => {
    if (user?.role === "admin") {
      fetch("http://localhost:8000/auth/users", {
        headers: { Authorization: `Bearer ${useAuthStore.getState().accessToken}` },
      })
        .then((r) => (r.ok ? r.json() : []))
        .then((data) => setUsersList(data))
        .catch(() => {});
    }
  }, [user]);

  const handleUpdateIdentity = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: JSON.stringify({
          display_name: displayName,
          email: email !== user?.email ? email : undefined,
          current_password: email !== user?.email ? currentPassword : undefined,
        }),
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to update profile");
      }

      updateUser({ display_name: displayName, email });
      setMessage({ type: "success", text: "Identity records updated successfully." });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setMessage({ type: "error", text: "New password and confirmation do not match." });
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to change station password");
      }

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage({ type: "success", text: "Station password successfully updated." });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const handleProvisionAnalyst = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch("http://localhost:8000/auth/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: JSON.stringify({
          email: provEmail,
          display_name: provName,
          password: provPassword,
          role: provRole,
        }),
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to provision analyst");
      }

      const data = await res.json();
      setUsersList((prev) => [...prev, data.user]);
      setProvEmail("");
      setProvName("");
      setProvPassword("");
      setMessage({ type: "success", text: `Provisioned station access for ${data.user.email}.` });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message });
    }
  };

  // Avatar Initials
  const initials = (user?.display_name || "OP")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Authenticated Station Operator
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Account & Security Profile
          </h1>
        </div>

        <button
          onClick={logout}
          className="px-4 py-2 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/30 text-[#FF4757] font-mono text-xs font-bold hover:bg-[#FF4757]/25 transition-all"
        >
          LOGOUT OF THIS STATION
        </button>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-lg border font-mono text-xs flex items-center gap-2.5 ${
            message.type === "success"
              ? "bg-[#4CAF7D]/15 border-[#4CAF7D]/30 text-[#4CAF7D]"
              : "bg-[#FF4757]/15 border-[#FF4757]/30 text-[#FF4757]"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <AlertTriangle className="w-4 h-4" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Grid: Identity + Security */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Identity & Session Details */}
        <div className="lg:col-span-6 space-y-5">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4 text-[#3FC7D4]" />
              Operator Identity & Call-Sign
            </h3>

            {/* Avatar & Role Header */}
            <div className="flex items-center gap-4 p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
              <div className="w-14 h-14 rounded-xl bg-[#3FC7D4]/20 border border-[#3FC7D4] flex items-center justify-center font-display font-bold text-lg text-[#3FC7D4] shadow-[0_0_15px_rgba(63,199,212,0.2)]">
                {initials}
              </div>
              <div className="space-y-1">
                <div className="text-base font-bold text-[#E7ECF5]">{user?.display_name}</div>
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                    style={{
                      backgroundColor:
                        user?.role === "admin" ? "rgba(255,138,61,0.15)" : "rgba(63,199,212,0.15)",
                      color: user?.role === "admin" ? "#FF8A3D" : "#3FC7D4",
                      border: `1px solid ${
                        user?.role === "admin" ? "rgba(255,138,61,0.4)" : "rgba(63,199,212,0.4)"
                      }`,
                    }}
                  >
                    {user?.role}
                  </span>
                  <span className="text-[#8A95AA]">{user?.email}</span>
                </div>
              </div>
            </div>

            {/* Edit Identity Form */}
            <form onSubmit={handleUpdateIdentity} className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Enclave Email Address</label>
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] font-bold hover:bg-[#3FC7D4]/25 transition-all text-xs"
              >
                SAVE IDENTITY CHANGES
              </button>
            </form>
          </div>

          {/* Session Metadata */}
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-3 font-mono text-xs">
            <h3 className="font-bold text-[#8A95AA] uppercase tracking-wider">
              Enclave Session Telemetry
            </h3>
            <div className="p-3 rounded bg-[#0B1220] border border-[#3FC7D4]/10 space-y-2">
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Last Station Login:</span>
                <span className="text-[#E7ECF5]">
                  {user?.last_login_at
                    ? new Date(user.last_login_at).toLocaleString()
                    : "Active Now"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Token Expiry:</span>
                <span className="text-[#3FC7D4]">60 Minutes (Rotating)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8A95AA]">Connection Type:</span>
                <span className="text-[#4CAF7D]">MUTUAL TLS / AIR-GAPPED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Security Credentials */}
        <div className="lg:col-span-6 space-y-5">
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-4">
            <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider flex items-center gap-2">
              <Key className="w-4 h-4 text-[#FF8A3D]" />
              Change Station Password
            </h3>

            <form onSubmit={handleChangePassword} className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Current Password</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">New Password (min 8 characters)</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Confirm New Password</label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2 rounded-lg bg-[#FF8A3D]/15 border border-[#FF8A3D]/30 text-[#FF8A3D] font-bold hover:bg-[#FF8A3D]/25 transition-all text-xs"
              >
                UPDATE STATION CREDENTIALS
              </button>
            </form>
          </div>

          {/* Admin User Provisioning (Admin Only) */}
          {user?.role === "admin" && (
            <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/25 space-y-4">
              <h3 className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-[#3FC7D4]" />
                  Admin: Provision New Analyst Account
                </span>
                <span className="text-[10px] text-[#3FC7D4]">RESTRICTED</span>
              </h3>

              <form onSubmit={handleProvisionAnalyst} className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[#8A95AA] text-[10px] uppercase">Analyst Email</label>
                    <input
                      type="text"
                      required
                      placeholder="analyst2@udtx.local"
                      value={provEmail}
                      onChange={(e) => setProvEmail(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                    />
                  </div>
                  <div>
                    <label className="text-[#8A95AA] text-[10px] uppercase">Display Name</label>
                    <input
                      type="text"
                      required
                      placeholder="Radar Specialist"
                      value={provName}
                      onChange={(e) => setProvName(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[#8A95AA] text-[10px] uppercase">Initial Password</label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={provPassword}
                      onChange={(e) => setProvPassword(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                    />
                  </div>
                  <div>
                    <label className="text-[#8A95AA] text-[10px] uppercase">Enclave Role</label>
                    <select
                      value={provRole}
                      onChange={(e) => setProvRole(e.target.value)}
                      className="w-full mt-1 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                    >
                      <option value="analyst">Analyst</option>
                      <option value="admin">Station Commander (Admin)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-2 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/30 text-[#3FC7D4] font-bold hover:bg-[#3FC7D4]/25 transition-all flex items-center justify-center gap-2"
                >
                  <Plus className="w-3.5 h-3.5" />
                  PROVISION ANALYST ACCOUNT
                </button>
              </form>

              {/* Active Users Table */}
              <div className="mt-4 pt-4 border-t border-[#3FC7D4]/15">
                <div className="text-[11px] font-mono text-[#8A95AA] mb-2 uppercase">
                  Provisioned Station Roster ({usersList.length})
                </div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto font-mono text-[11px]">
                  {usersList.map((u) => (
                    <div
                      key={u.id}
                      className="p-2 rounded bg-[#0B1220] border border-[#3FC7D4]/10 flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-[#E7ECF5]">{u.display_name}</span>
                        <span className="text-[#8A95AA] ml-2 text-[10px]">({u.email})</span>
                      </div>
                      <span className="text-[#3FC7D4] uppercase text-[10px] font-bold">
                        {u.role}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
