import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Shield,
  Download,
  Trash2,
  Edit3,
  UserPlus,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  HardDrive,
  Database,
  ExternalLink,
  Lock,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";
import { useAuthStore, apiFetch } from "../lib/auth";
import { getApiBaseUrl } from "../lib/apiConfig";
import { getStorageQuota, type StorageQuotaInfo } from "../lib/pwa";
import { SEO } from "../components/SEO";

interface Grievance {
  id: string;
  subject: string;
  body: string;
  status: string;
  created_at: string;
  ack_target_at: string;
  resolution_target_at: string;
  resolved_at: string | null;
  resolution_notes?: string | null;
}

interface Nominee {
  full_name: string;
  contact: string;
  relationship: string;
  designated_at: string;
  status: string;
}

export const PrivacyCenterPage: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"access" | "erasure" | "grievances" | "nominee" | "cookies">("access");

  // State
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const [nominee, setNominee] = useState<Nominee | null>(null);
  const [nomineeName, setNomineeName] = useState("");
  const [nomineeContact, setNomineeContact] = useState("");
  const [nomineeRelationship, setNomineeRelationship] = useState("");
  const [nomineeSaving, setNomineeSaving] = useState(false);
  const [nomineeMsg, setNomineeMsg] = useState<string | null>(null);

  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [grievanceSubject, setGrievanceSubject] = useState("");
  const [grievanceBody, setGrievanceBody] = useState("");
  const [grievanceSubmitting, setGrievanceSubmitting] = useState(false);
  const [grievanceMsg, setGrievanceMsg] = useState<string | null>(null);

  // Deletion Modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deletePhrase, setDeletePhrase] = useState("");
  const [deleteSubmitting, setDeleteSubmitting] = useState(false);
  const [deleteResult, setDeleteResult] = useState<any | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Storage Quota
  const [quotaInfo, setQuotaInfo] = useState<StorageQuotaInfo | null>(null);
  const [retentionStatus, setRetentionStatus] = useState<any | null>(null);
  const [purgeResult, setPurgeResult] = useState<string | null>(null);

  const api = getApiBaseUrl();

  useEffect(() => {
    loadNominee();
    loadGrievances();
    loadStorageQuota();
    loadRetentionStatus();
  }, []);

  const loadStorageQuota = async () => {
    const info = await getStorageQuota();
    setQuotaInfo(info);
  };

  const loadRetentionStatus = async () => {
    try {
      const res = await apiFetch(`${api}/privacy/retention-status`);
      if (res.ok) {
        const data = await res.json();
        setRetentionStatus(data);
      }
    } catch (e) {}
  };

  const loadNominee = async () => {
    try {
      const res = await apiFetch(`${api}/privacy/nominee`);
      if (res.ok) {
        const data = await res.json();
        if (data.designated && data.nominee) {
          setNominee(data.nominee);
          setNomineeName(data.nominee.full_name);
          setNomineeContact(data.nominee.contact);
          setNomineeRelationship(data.nominee.relationship);
        }
      }
    } catch (e) {
      console.debug("Failed to load nominee:", e);
    }
  };

  const loadGrievances = async () => {
    try {
      const res = await apiFetch(`${api}/privacy/grievances`);
      if (res.ok) {
        const data = await res.json();
        setGrievances(data);
      }
    } catch (e) {
      console.debug("Failed to load grievances:", e);
    }
  };

  const handleDownloadExport = async () => {
    setIsExporting(true);
    setExportSuccess(false);
    try {
      const res = await apiFetch(`${api}/privacy/export`);
      if (!res.ok) throw new Error("Data export generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `udtx_dpdp_export_${user?.id || "account"}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 4000);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleSaveNominee = async (e: React.FormEvent) => {
    e.preventDefault();
    setNomineeSaving(true);
    setNomineeMsg(null);
    try {
      const res = await apiFetch(`${api}/privacy/nominee`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: nomineeName,
          contact: nomineeContact,
          relationship: nomineeRelationship,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to designate nominee");
      }
      const data = await res.json();
      setNominee(data.nominee);
      setNomineeMsg("Trusted nominee contact registered successfully under DPDP Act S.14.");
    } catch (err: any) {
      setNomineeMsg(err.message || "Failed to save nominee");
    } finally {
      setNomineeSaving(false);
    }
  };

  const handleSubmitGrievance = async (e: React.FormEvent) => {
    e.preventDefault();
    setGrievanceSubmitting(true);
    setGrievanceMsg(null);
    try {
      const res = await apiFetch(`${api}/privacy/grievances`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: grievanceSubject,
          body: grievanceBody,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Grievance submission rejected");
      }
      const data = await res.json();
      setGrievances((prev) => [data.grievance, ...prev]);
      setGrievanceSubject("");
      setGrievanceBody("");
      setGrievanceMsg(`Grievance ${data.grievance.id} submitted. Acknowledgment due within 48h.`);
    } catch (err: any) {
      setGrievanceMsg(err.message || "Failed to file grievance");
    } finally {
      setGrievanceSubmitting(false);
    }
  };

  const handleRequestErasure = async (e: React.FormEvent) => {
    e.preventDefault();
    setDeleteSubmitting(true);
    setDeleteError(null);
    try {
      const res = await apiFetch(`${api}/privacy/request-erasure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          password: deletePassword,
          confirmation_phrase: deletePhrase,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Erasure authorization failed");
      }
      const data = await res.json();
      setDeleteResult(data.details);
    } catch (err: any) {
      setDeleteError(err.message || "Failed to schedule erasure");
    } finally {
      setDeleteSubmitting(false);
    }
  };

  const handleTriggerRetentionPurge = async () => {
    try {
      const res = await apiFetch(`${api}/privacy/purge-expired`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setPurgeResult(`Purge executed. ${data.records_purged} expired records pruned. Certificate: ${data.audit_certificate}`);
        loadRetentionStatus();
        setTimeout(() => setPurgeResult(null), 5000);
      }
    } catch (err) {
      console.error("Purge error:", err);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <SEO
        title="Privacy Center | Data Principal Rights Console — UDT-X"
        description="Exercise statutory rights under India's Digital Personal Data Protection Act 2023 (DPDP Act). Download personal dossiers, request erasure, file grievances, and designate nominees."
        noIndex={true}
      />

      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2 font-mono text-xs text-[#3FC7D4]">
            <Lock className="w-3.5 h-3.5 text-[#3FC7D4]" />
            <span className="font-bold uppercase tracking-wider">
              India DPDP Act 2023 Enforcement Console
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Station Privacy Center
          </h1>
          <p className="text-xs text-[#8A95AA] mt-0.5">
            Directly exercise your enforceable rights as a Data Principal under Sections 11–14 of the Digital Personal Data Protection Act, 2023.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 rounded-lg bg-[#131B2E] border border-[#4CAF7D]/30 text-[#4CAF7D] font-bold flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>DPDP ACT 2023 COMPLIANT</span>
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-[#3FC7D4]/15 pb-3 font-mono text-xs">
        {[
          { id: "access", label: "S.11 RIGHT TO ACCESS", icon: Download },
          { id: "erasure", label: "S.12 CORRECTION & ERASURE", icon: Trash2 },
          { id: "grievances", label: "S.13 GRIEVANCE REDRESSAL", icon: FileText },
          { id: "nominee", label: "S.14 RIGHT TO NOMINATE", icon: UserPlus },
          { id: "cookies", label: "COOKIE & STORAGE INVENTORY", icon: Database },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all font-bold ${
                isActive
                  ? "bg-[#3FC7D4]/15 border border-[#3FC7D4] text-[#3FC7D4] shadow-[0_0_12px_rgba(63,199,212,0.15)]"
                  : "bg-[#131B2E] border border-[#3FC7D4]/15 text-[#8A95AA] hover:text-[#E7ECF5] hover:border-[#3FC7D4]/40"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: SECTION 11 — RIGHT TO ACCESS */}
      {activeTab === "access" && (
        <div className="space-y-5">
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4]">
                <Download className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-display font-bold text-[#E7ECF5]">
                  Section 11: Right to Access Information About Personal Data
                </h2>
                <p className="text-xs font-mono text-[#8A95AA]">
                  Obtain a summary of personal data being processed, identifiable identities, and lawful disclosure audit logs.
                </p>
              </div>
            </div>

            <p className="text-xs text-[#8A95AA] leading-relaxed">
              Under Section 11 of the Digital Personal Data Protection Act 2023, you have the right to receive an export of all personal data, user preferences, authentication events, and grievance records associated with your Data Principal identity.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                <div className="text-[#8A95AA] text-[10px]">OPERATOR ACCOUNT</div>
                <div className="text-[#E7ECF5] font-bold mt-1 truncate">{user?.email}</div>
                <div className="text-[10px] text-[#3FC7D4] mt-0.5">Role: {user?.role.toUpperCase()}</div>
              </div>
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                <div className="text-[#8A95AA] text-[10px]">DATA PRINCIPAL ID</div>
                <div className="text-[#E7ECF5] font-bold mt-1 font-mono text-[11px] truncate">{user?.id}</div>
                <div className="text-[10px] text-[#4CAF7D] mt-0.5">Hardware Enclave Node</div>
              </div>
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                <div className="text-[#8A95AA] text-[10px]">EXPORT FORMAT</div>
                <div className="text-[#E7ECF5] font-bold mt-1">Machine-Readable JSON</div>
                <div className="text-[10px] text-[#8A95AA] mt-0.5">Includes CERT-In Disclosures</div>
              </div>
            </div>

            <div className="pt-2 flex items-center gap-3">
              <button
                onClick={handleDownloadExport}
                disabled={isExporting}
                className="px-5 py-2.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-mono text-xs font-bold hover:bg-[#3FC7D4]/90 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(63,199,212,0.25)] active:scale-[0.98] disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                <span>{isExporting ? "GENERATING ENCLAVE EXPORT..." : "DOWNLOAD COMPLETE DATA DOSSIER (.JSON)"}</span>
              </button>

              {exportSuccess && (
                <span className="font-mono text-xs text-[#4CAF7D] flex items-center gap-1.5 animate-fade-in">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Dossier downloaded successfully.</span>
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SECTION 12 — CORRECTION & ERASURE */}
      {activeTab === "erasure" && (
        <div className="space-y-5">
          {/* Correction Section */}
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4]">
                  <Edit3 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-display font-bold text-[#E7ECF5]">
                    Section 12(1): Right to Correction and Updating
                  </h2>
                  <p className="text-xs font-mono text-[#8A95AA]">
                    Correction of inaccurate or misleading personal data.
                  </p>
                </div>
              </div>

              <Link
                to="/app/profile"
                className="px-4 py-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/30 hover:border-[#3FC7D4] text-[#3FC7D4] font-mono text-xs font-bold transition-all flex items-center gap-2"
              >
                <span>OPEN PROFILE EDITOR</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
            <p className="text-xs text-[#8A95AA] leading-relaxed">
              Update your display name, password credentials, and station email address at any time through the authenticated station Profile console.
            </p>
          </div>

          {/* Erasure Section */}
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#FF4757]/30 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/40 flex items-center justify-center text-[#FF4757]">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-display font-bold text-[#E7ECF5]">
                  Section 12(2)–(3): Right to Erasure & Statutory Retentions
                </h2>
                <p className="text-xs font-mono text-[#8A95AA]">
                  Request permanent erasure of personal data, subject to lawful ongoing obligations.
                </p>
              </div>
            </div>

            {/* Legal Accuracy Notice */}
            <div className="p-4 rounded-lg bg-[#0B1220] border border-[#FF8A3D]/30 space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2 text-[#FF8A3D] font-bold">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>LEGAL BOUNDS OF ERASURE UNDER DPDP ACT 2023 & CERT-IN DIRECTIONS</span>
              </div>
              <p className="text-[#8A95AA] leading-relaxed">
                Under Section 12(3) of India's DPDP Act 2023, the right to erasure does not require the deletion of personal data where specified retention is necessary for compliance with any law or for a legitimate defense purpose.
              </p>
              <ul className="list-disc list-inside text-[#8A95AA] space-y-1 pl-2 text-[11px]">
                <li><strong className="text-[#E7ECF5]">Erased Immediately:</strong> Account credentials, display names, nominee designations, browser notification channels, and UI personalization preferences.</li>
                <li><strong className="text-[#FF8A3D]">Legally Retained (180 Days):</strong> Authentication timestamps, source IP addresses, and command audit trails are mandated to be retained for 180 days pursuant to the Indian Computer Emergency Response Team (CERT-In) Cyber Security Directions.</li>
              </ul>
            </div>

            <button
              onClick={() => {
                setShowDeleteModal(true);
                setDeleteResult(null);
                setDeleteError(null);
              }}
              className="px-5 py-2.5 rounded-lg bg-[#FF4757]/15 border border-[#FF4757]/40 text-[#FF4757] font-mono text-xs font-bold hover:bg-[#FF4757]/25 transition-all flex items-center gap-2 active:scale-[0.98]"
            >
              <Trash2 className="w-4 h-4" />
              <span>REQUEST ACCOUNT ERASURE</span>
            </button>
          </div>
        </div>
      )}

      {/* TAB 3: SECTION 13 — GRIEVANCE REDRESSAL */}
      {activeTab === "grievances" && (
        <div className="space-y-5">
          {/* Statutory Response SLA Banner */}
          <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs space-y-2">
            <div className="flex items-center gap-2 text-[#3FC7D4] font-bold uppercase tracking-wider">
              <Clock className="w-4 h-4" />
              <span>Statutory Grievance Redressal Timeline (DPDP Act Section 13)</span>
            </div>
            <p className="text-[#8A95AA] leading-relaxed">
              As required by the DPDP Act 2023, UDT-X publishes binding response timelines for all Data Principal grievances:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                <div className="text-[#8A95AA] text-[10px]">MANDATORY ACKNOWLEDGMENT</div>
                <div className="text-[#3FC7D4] font-bold text-sm mt-0.5">Within 48 Hours</div>
                <div className="text-[10px] text-[#8A95AA] mt-0.5">Ticket ID & designated Data Protection Officer response</div>
              </div>
              <div className="p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                <div className="text-[#8A95AA] text-[10px]">RESOLUTION TARGET</div>
                <div className="text-[#4CAF7D] font-bold text-sm mt-0.5">Within 7 Calendar Days</div>
                <div className="text-[10px] text-[#8A95AA] mt-0.5">Full formal redressal, corrective action, or legal rationale</div>
              </div>
            </div>
          </div>

          {/* Submission Form */}
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4">
            <h3 className="text-sm font-bold font-display text-[#E7ECF5]">File a Tracked Privacy Grievance</h3>
            <form onSubmit={handleSubmitGrievance} className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Grievance Subject</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Telemetry IP Masking Inquiry / Data Portability Verification"
                  value={grievanceSubject}
                  onChange={(e) => setGrievanceSubject(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>
              <div>
                <label className="text-[#8A95AA] text-[10px] uppercase">Description & Specific Concerns</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Provide detailed description of the data processing concern or requested correction under DPDP Act provisions..."
                  value={grievanceBody}
                  onChange={(e) => setGrievanceBody(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                />
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  type="submit"
                  disabled={grievanceSubmitting}
                  className="px-5 py-2.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold hover:bg-[#3FC7D4]/90 transition-all disabled:opacity-50"
                >
                  {grievanceSubmitting ? "FILING GRIEVANCE..." : "SUBMIT FORMAL GRIEVANCE"}
                </button>

                {grievanceMsg && (
                  <span className="text-[#4CAF7D] text-xs font-mono">{grievanceMsg}</span>
                )}
              </div>
            </form>
          </div>

          {/* Tracked Grievances Table */}
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/15 space-y-3 font-mono text-xs">
            <h3 className="text-xs font-bold text-[#8A95AA] uppercase tracking-wider">
              Tracked Grievance Roster ({grievances.length})
            </h3>
            {grievances.length === 0 ? (
              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 text-center text-[#8A95AA]">
                No grievances on record for this Data Principal identity.
              </div>
            ) : (
              <div className="space-y-3">
                {grievances.map((g) => (
                  <div key={g.id} className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#E7ECF5]">{g.id}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                            g.status === "RESOLVED"
                              ? "bg-[#4CAF7D]/15 text-[#4CAF7D] border border-[#4CAF7D]/40"
                              : "bg-[#FF8A3D]/15 text-[#FF8A3D] border border-[#FF8A3D]/40"
                          }`}
                        >
                          {g.status}
                        </span>
                      </div>
                      <span className="text-[#8A95AA] text-[10px]">
                        Filed: {new Date(g.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="font-bold text-[#E7ECF5]">{g.subject}</div>
                    <p className="text-[#8A95AA] text-[11px] leading-relaxed">{g.body}</p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 text-[10px] border-t border-[#3FC7D4]/10">
                      <div>
                        <span className="text-[#8A95AA]">Ack SLA Deadline: </span>
                        <span className="text-[#3FC7D4]">{new Date(g.ack_target_at).toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-[#8A95AA]">Resolution SLA Deadline: </span>
                        <span className="text-[#4CAF7D]">{new Date(g.resolution_target_at).toLocaleString()}</span>
                      </div>
                    </div>

                    {g.resolution_notes && (
                      <div className="p-2.5 rounded bg-[#4CAF7D]/10 border border-[#4CAF7D]/20 text-[11px] text-[#4CAF7D] mt-2">
                        <strong className="block text-[10px] uppercase">Official DPO Resolution:</strong>
                        {g.resolution_notes}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: SECTION 14 — RIGHT TO NOMINATE */}
      {activeTab === "nominee" && (
        <div className="space-y-5">
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4]">
                <UserPlus className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-display font-bold text-[#E7ECF5]">
                  Section 14: Right to Nominate Trusted Representative
                </h2>
                <p className="text-xs font-mono text-[#8A95AA]">
                  Designate an individual who shall exercise your Data Principal rights in the event of death or incapacity.
                </p>
              </div>
            </div>

            <p className="text-xs text-[#8A95AA] leading-relaxed">
              India's DPDP Act 2023 provides a distinct statutory right under Section 14 (not present in GDPR or CCPA) allowing a Data Principal to designate another individual to exercise their rights to access, correction, or erasure in the event of death or incapacity.
            </p>

            {nominee && (
              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#4CAF7D]/30 space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#4CAF7D] font-bold flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    ACTIVE NOMINEE ON FILE
                  </span>
                  <span className="text-[#8A95AA] text-[10px]">
                    Designated: {new Date(nominee.designated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-[11px]">
                  <div>
                    <span className="text-[#8A95AA] block text-[10px]">NAME</span>
                    <span className="text-[#E7ECF5] font-bold">{nominee.full_name}</span>
                  </div>
                  <div>
                    <span className="text-[#8A95AA] block text-[10px]">CONTACT DETAILS</span>
                    <span className="text-[#E7ECF5] font-bold">{nominee.contact}</span>
                  </div>
                  <div>
                    <span className="text-[#8A95AA] block text-[10px]">RELATIONSHIP</span>
                    <span className="text-[#3FC7D4] font-bold">{nominee.relationship}</span>
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={handleSaveNominee} className="space-y-4 font-mono text-xs pt-2">
              <h3 className="text-xs font-bold text-[#8A95AA] uppercase tracking-wider">
                {nominee ? "Update Nominee Designation" : "Appoint New Trusted Nominee"}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="text-[#8A95AA] text-[10px] uppercase">Nominee Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Major Vikramaditya Rathore"
                    value={nomineeName}
                    onChange={(e) => setNomineeName(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                  />
                </div>
                <div>
                  <label className="text-[#8A95AA] text-[10px] uppercase">Contact Phone / Email</label>
                  <input
                    type="text"
                    required
                    placeholder="+91-98765-43210 or nominee@enclave.in"
                    value={nomineeContact}
                    onChange={(e) => setNomineeContact(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                  />
                </div>
                <div>
                  <label className="text-[#8A95AA] text-[10px] uppercase">Relationship / Capacity</label>
                  <input
                    type="text"
                    required
                    placeholder="Designated Kin / Secondary Keyholder"
                    value={nomineeRelationship}
                    onChange={(e) => setNomineeRelationship(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 text-[#E7ECF5] focus:outline-none focus:border-[#3FC7D4]"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  type="submit"
                  disabled={nomineeSaving}
                  className="px-5 py-2.5 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold hover:bg-[#3FC7D4]/90 transition-all disabled:opacity-50"
                >
                  {nomineeSaving ? "RECORDING NOMINEE..." : "RECORD NOMINEE DESIGNATION"}
                </button>

                {nomineeMsg && (
                  <span className="text-[#4CAF7D] text-xs font-mono">{nomineeMsg}</span>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TAB 5: COOKIE & STORAGE INVENTORY */}
      {activeTab === "cookies" && (
        <div className="space-y-5">
          {/* Specific Cookie Inventory Table */}
          <div className="p-6 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#3FC7D4]/15 border border-[#3FC7D4]/40 flex items-center justify-center text-[#3FC7D4]">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-display font-bold text-[#E7ECF5]">
                  Enclave Cookie & Storage Inventory
                </h2>
                <p className="text-xs font-mono text-[#8A95AA]">
                  Explicit cryptographic inventory of all client-side cookies and persistent storage tokens.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full font-mono text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#3FC7D4]/20 text-[#8A95AA] text-[10px] text-left">
                    <th className="py-2.5 px-3">IDENTIFIER</th>
                    <th className="py-2.5 px-3">CATEGORY</th>
                    <th className="py-2.5 px-3">PURPOSE & ENCLAVE FUNCTION</th>
                    <th className="py-2.5 px-3">SECURITY ATTRIBUTES</th>
                    <th className="py-2.5 px-3">EXPIRY</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#3FC7D4]/10">
                  <tr>
                    <td className="py-3 px-3 font-bold text-[#3FC7D4]">udtx_refresh_token</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#3FC7D4]/15 text-[#3FC7D4] border border-[#3FC7D4]/30">
                        Strictly Necessary
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[#E7ECF5]">
                      Carries JWT refresh session token for silent station re-authentication. Unreadable by JavaScript.
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA] text-[11px]">
                      HttpOnly, Secure, SameSite=Lax, Path=/
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA]">7 Days</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-3 font-bold text-[#3FC7D4]">udtx_auth_store</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#3FC7D4]/15 text-[#3FC7D4] border border-[#3FC7D4]/30">
                        Strictly Necessary
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[#E7ECF5]">
                      Stores user session profile, operator call-sign, and UI alerting preferences. (JWT Access Token is memory-only).
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA] text-[11px]">
                      Browser LocalStorage (Non-tokenized)
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA]">Persistent</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-3 font-bold text-[#3FC7D4]">udtx_analytics_consent</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-[#4CAF7D]/15 text-[#4CAF7D] border border-[#4CAF7D]/30">
                        Functional / Consent
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[#E7ECF5]">
                      Records operator consent decision from the compliance banner. Zero tracking occurs before opt-in.
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA] text-[11px]">
                      Browser LocalStorage
                    </td>
                    <td className="py-3 px-3 text-[#8A95AA]">1 Year</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Storage Quota Awareness & CERT-In Retention Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 font-mono text-xs">
            {/* Storage Quota */}
            <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3">
              <div className="flex items-center gap-2 text-[#3FC7D4] font-bold">
                <HardDrive className="w-4 h-4" />
                <span>Client Storage Quota Awareness</span>
              </div>
              <p className="text-[11px] text-[#8A95AA]">
                Live estimate via <code className="text-[#3FC7D4]">navigator.storage.estimate()</code>. Automatic trimming triggers if usage exceeds 80% to prevent unpredictable browser cache eviction.
              </p>
              {quotaInfo ? (
                <div className="space-y-2 p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10">
                  <div className="flex justify-between">
                    <span className="text-[#8A95AA]">Cache Storage Used:</span>
                    <span className="text-[#E7ECF5] font-bold">{quotaInfo.usageMB} MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8A95AA]">Allocated Browser Quota:</span>
                    <span className="text-[#E7ECF5] font-bold">{quotaInfo.quotaMB} MB</span>
                  </div>
                  <div className="w-full bg-[#131B2E] h-2 rounded-full overflow-hidden mt-1">
                    <div
                      className={`h-full ${quotaInfo.isNearQuota ? "bg-[#FF4757]" : "bg-[#3FC7D4]"}`}
                      style={{ width: `${Math.max(1, quotaInfo.usagePercent)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-[#4CAF7D] text-right">
                    {quotaInfo.usagePercent}% capacity — HEALTHY
                  </div>
                </div>
              ) : (
                <div className="text-[#8A95AA]">Calculating browser storage...</div>
              )}
            </div>

            {/* Retention Schedule */}
            <div className="p-5 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 space-y-3">
              <div className="flex items-center gap-2 text-[#4CAF7D] font-bold">
                <Database className="w-4 h-4" />
                <span>CERT-In 180-Day Data Retention Job</span>
              </div>
              <p className="text-[11px] text-[#8A95AA]">
                Statutory audit log retention cycle under CERT-In Directions and DPDP Act S.12(3). Records older than 180 days are securely expunged.
              </p>
              {retentionStatus && (
                <div className="space-y-1.5 p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/10 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-[#8A95AA]">Retention Window:</span>
                    <span className="text-[#E7ECF5]">{retentionStatus.retention_days} Days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8A95AA]">Active Audit Records:</span>
                    <span className="text-[#3FC7D4] font-bold">{retentionStatus.active_audit_records}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8A95AA]">Next Scheduled Purge:</span>
                    <span className="text-[#E7ECF5]">{retentionStatus.next_scheduled_purge}</span>
                  </div>
                </div>
              )}

              {user?.role === "admin" && (
                <button
                  onClick={handleTriggerRetentionPurge}
                  className="w-full py-2 rounded-lg bg-[#131B2E] border border-[#4CAF7D]/40 text-[#4CAF7D] hover:bg-[#4CAF7D]/10 font-bold transition-all text-xs"
                >
                  RUN RETENTION PURGE JOB (ADMIN)
                </button>
              )}

              {purgeResult && (
                <div className="p-2 rounded bg-[#4CAF7D]/15 border border-[#4CAF7D]/30 text-[#4CAF7D] text-[10px]">
                  {purgeResult}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Account Deletion Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-[#0B1220]/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg p-6 rounded-2xl bg-[#131B2E] border border-[#FF4757]/40 shadow-2xl space-y-4 font-mono text-xs">
            <div className="flex items-center gap-2 text-[#FF4757] font-bold text-sm">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>CONFIRM DATA PRINCIPAL ERASURE REQUEST</span>
            </div>

            {!deleteResult ? (
              <form onSubmit={handleRequestErasure} className="space-y-3">
                <p className="text-[#8A95AA] leading-relaxed">
                  You are initiating an account erasure under Section 12 of the DPDP Act 2023. Profile data and custom configurations will be queued for permanent destruction. Required security audit records will be retained for 180 days per CERT-In compliance.
                </p>

                {deleteError && (
                  <div className="p-2 rounded bg-[#FF4757]/15 border border-[#FF4757]/30 text-[#FF4757]">
                    {deleteError}
                  </div>
                )}

                <div>
                  <label className="text-[#8A95AA] text-[10px] uppercase">Station Password</label>
                  <input
                    type="password"
                    required
                    placeholder="Enter station password..."
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#FF4757]/30 text-[#E7ECF5] focus:outline-none focus:border-[#FF4757]"
                  />
                </div>

                <div>
                  <label className="text-[#8A95AA] text-[10px] uppercase">
                    Type <span className="text-[#FF4757] font-bold">PERMANENTLY DELETE</span> to confirm
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="PERMANENTLY DELETE"
                    value={deletePhrase}
                    onChange={(e) => setDeletePhrase(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#FF4757]/30 text-[#E7ECF5] focus:outline-none focus:border-[#FF4757]"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowDeleteModal(false)}
                    className="px-4 py-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5]"
                  >
                    CANCEL
                  </button>
                  <button
                    type="submit"
                    disabled={deleteSubmitting}
                    className="px-4 py-2 rounded-lg bg-[#FF4757] text-white font-bold hover:bg-[#FF4757]/90 disabled:opacity-50"
                  >
                    {deleteSubmitting ? "PROCESSING..." : "CONFIRM ERASURE SCHEDULE"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                <div className="p-3 rounded bg-[#4CAF7D]/15 border border-[#4CAF7D]/30 text-[#4CAF7D] font-bold">
                  Erasure Schedule Confirmed (Ticket: {deleteResult.erasure_id})
                </div>
                <div className="text-[11px] text-[#8A95AA] space-y-1">
                  <div><strong>Account:</strong> {deleteResult.user_email}</div>
                  <div><strong>Cooloff Expiry:</strong> {new Date(deleteResult.scheduled_erasure_at).toLocaleDateString()}</div>
                </div>
                <div className="p-3 rounded bg-[#0B1220] border border-[#3FC7D4]/15 space-y-1 text-[10px] text-[#8A95AA]">
                  <strong className="text-[#E7ECF5] block">Itemized Legal Breakdown:</strong>
                  <div>• Personal identity fields & UI tokens: Erased immediately</div>
                  <div>• Authentication audit log: Retained for 180 days under CERT-In Directions S.12(3)</div>
                </div>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="w-full py-2 rounded-lg bg-[#3FC7D4] text-[#0B1220] font-bold"
                >
                  CLOSE
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
