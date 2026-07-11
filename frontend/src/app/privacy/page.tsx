"use client";

import React, { useState } from "react";
import { ShieldCheck, Calendar, Server, Trash2, Key, Info, CheckCircle } from "lucide-react";
import { apiService } from "@/lib/api";

export default function PrivacyPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePurgeRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    try {
      const res = await apiService.requestDataDeletion(email);
      setSubmitted(true);
      setMessage(res.message || "Your erasure request has been logged. Audio is already deleted immediately upon assessment; database scoring parameters will be wiped.");
    } catch (err: any) {
      alert("Failed to submit erasure request. Please verify the email formatting.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8 space-y-12">
      
      {/* Header section */}
      <div className="text-center space-y-4">
        <div className="mx-auto w-12 h-12 rounded-full bg-emerald-950/30 border border-emerald-900/50 flex items-center justify-center text-emerald-500">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          DPDP Act 2023 Compliance & Privacy Notice
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Disclosures on how AuraPronounce protects, encrypts, and handles voice recordings and personal identifiers under India's Digital Personal Data Protection Act (DPDP), 2023.
        </p>
      </div>

      {/* Grid: Main disclosures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Core Block 1: Purpose Limitation */}
        <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-emerald-500" />
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <Info className="w-4 h-4 text-emerald-400" />
            <span>Purpose Limitation</span>
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Your audio and voice profile are processed strictly for the purpose of English pronunciation assessment (acoustic metrics, word-level scores, and phonetic alignment). Your recording will never be sold, used for voice profiling, or repurposed for marketing.
          </p>
        </div>

        {/* Core Block 2: Data Retention & Cleanup */}
        <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-emerald-500" />
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <Calendar className="w-4 h-4 text-emerald-400" />
            <span>Audio Deletion Policy</span>
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Under our minimal data retention schedule, raw audio files are deleted from backend storage <strong>immediately</strong> upon completion of analysis (typically within 10-30 seconds of upload). Leftover temporary files are swept automatically by worker tasks every 24 hours.
          </p>
        </div>

        {/* Core Block 3: Encryption At Rest */}
        <div className="glass-panel rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-emerald-500" />
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <Key className="w-4 h-4 text-emerald-400" />
            <span>AES-256 Encryption</span>
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All personal identifiers, including email records, client IP addresses in consent audits, and logs, are stored encrypted at rest using AES-256 algorithms. Only anonymous, aggregate scoring percentages are visible in metrics tables.
          </p>
        </div>

        {/* Core Block 4: Data Residency */}
        <div className="glass-panel rounded-xl p-6 relative overflow-hidden" id="data-residency">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-emerald-500" />
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>India Data Residency</span>
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All primary SQL servers, Redis queue caches, and file storage volumes are provisioned in the India region (AWS Mumbai <code>ap-south-1</code> / Supabase India databases) to comply with data residency standards.
          </p>
        </div>

      </div>

      {/* Right to Erasure Request Box */}
      <div className="glass-panel rounded-xl p-8 relative overflow-hidden" id="deletion">
        <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-emerald-500 to-teal-500" />
        
        <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-2">
          <Trash2 className="w-5 h-5 text-emerald-400" />
          <span>Right to Erasure (Delete My Account & Data)</span>
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          Submit your registered email address to completely wipe your assessment histories, metadata logs, and user account from our databases.
        </p>

        {submitted ? (
          <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/50 text-emerald-400 text-sm flex items-center gap-2">
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
            <span>{message}</span>
          </div>
        ) : (
          <form onSubmit={handlePurgeRequest} className="space-y-4 max-w-md">
            <div>
              <label htmlFor="purge-email" className="block text-xs font-semibold text-slate-400 mb-1">
                Your Registered Email
              </label>
              <input
                id="purge-email"
                type="email"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
            >
              {loading && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              <span>Submit Purge Request</span>
            </button>
          </form>
        )}
      </div>

    </div>
  );
}
