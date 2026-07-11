"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { MessageSquareCode, ShieldCheck, LogIn, LogOut, User, Lock, Mail, X } from "lucide-react";
import { apiService } from "@/lib/api";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup" | "forgot">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const pathname = usePathname();

  // Close modal and reset form on route change
  useEffect(() => {
    setAuthModalOpen(false);
    resetForm();
  }, [pathname]);

  // Load user session on boot
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedEmail = localStorage.getItem("user_email");
      if (storedEmail) {
        setUserEmail(storedEmail);
      }
    }
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!email || (authMode !== "forgot" && !password)) {
      setErrorMsg("Please fill in all required fields.");
      return;
    }

    try {
      if (authMode === "login") {
        // Sign In Flow
        const data = await apiService.login(email, password);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user_email", email);
        setUserEmail(email);
        setSuccessMsg("Logged in successfully!");
        setTimeout(() => {
          setAuthModalOpen(false);
          resetForm();
          window.location.reload(); // Refresh token context
        }, 1000);
      } else if (authMode === "signup") {
        // Sign Up Flow
        await apiService.register(email, password);
        setSuccessMsg("Account created successfully! Please sign in.");
        setAuthMode("login"); // Toggle to login mode
        setPassword("");
      } else if (authMode === "forgot") {
        // Forgot Password Flow
        const data = await apiService.forgotPassword(email);
        setSuccessMsg(data.message || "Password reset simulated. Check server logs!");
        setEmail("");
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Request failed. Try again.");
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_email");
    setUserEmail(null);
    window.location.reload();
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const switchMode = (mode: "login" | "signup" | "forgot") => {
    resetForm();
    setAuthMode(mode);
  };

  return (
    <>
      {/* Navigation Header */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/70 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2 text-xl font-bold tracking-tight bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
            <MessageSquareCode className="w-6 h-6 text-violet-500" />
            <span>AuraPronounce</span>
          </Link>
          
          <nav className="flex items-center space-x-6 text-sm font-medium text-slate-300">
            <Link href="/" className="hover:text-violet-400 transition-colors">Home</Link>
            <Link href="/upload" className="hover:text-violet-400 transition-colors">Assess Speech</Link>
            <Link href="/privacy" className="hover:text-violet-400 transition-colors flex items-center gap-1">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span>DPDP Compliance</span>
            </Link>

            {/* Auth Buttons */}
            {userEmail ? (
              <div className="flex items-center gap-4 border-l border-slate-800 pl-4">
                <div className="flex items-center gap-1.5 text-slate-400">
                  <User className="w-4 h-4 text-violet-500" />
                  <span className="max-w-[120px] truncate text-xs">{userEmail}</span>
                </div>
                <button 
                  onClick={handleSignOut}
                  className="flex items-center gap-1 bg-slate-900 border border-slate-800 hover:bg-slate-800 px-3 py-1.5 rounded-lg text-slate-300 hover:text-white transition-all text-xs"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <button 
                onClick={() => { resetForm(); setAuthModalOpen(true); }}
                className="flex items-center gap-1 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 px-4 py-1.5 rounded-lg text-white font-semibold transition-all text-xs"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In / Sign Up</span>
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Glassmorphic Auth Modal */}
      {authModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl w-full max-w-md p-6 relative shadow-2xl overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
            
            <button 
              onClick={() => setAuthModalOpen(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-6">
              <h3 className="text-xl font-bold text-white">
                {authMode === "login" && "Sign In to AuraPronounce"}
                {authMode === "signup" && "Create an Account"}
                {authMode === "forgot" && "Forgot Password"}
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                {authMode === "login" && "Track your pronunciation scores and histories"}
                {authMode === "signup" && "Join to save your speech feedback logs securely"}
                {authMode === "forgot" && "Enter your email to simulate a reset link"}
              </p>
            </div>

            <form onSubmit={handleAuth} className="space-y-4" autoComplete="off">
              {errorMsg && (
                <div className="p-3 rounded-lg bg-red-950/40 border border-red-900/50 text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}
              {successMsg && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-900/50 text-emerald-400 text-xs">
                  {successMsg}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>Email Address</span>
                </label>
                <input 
                  type="email"
                  placeholder="name@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                  required
                  autoComplete="off"
                />
              </div>

              {authMode !== "forgot" && (
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                      <Lock className="w-3.5 h-3.5 text-slate-500" />
                      <span>Password</span>
                    </label>
                    {authMode === "login" && (
                      <button 
                        type="button"
                        onClick={() => switchMode("forgot")}
                        className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                      >
                        Forgot Password?
                      </button>
                    )}
                  </div>
                  <input 
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500 transition-colors"
                    autoComplete="new-password"
                    required
                  />
                </div>
              )}

              <button 
                type="submit"
                className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 py-2.5 rounded-lg text-white font-semibold text-sm transition-all mt-6"
              >
                {authMode === "login" && "Sign In"}
                {authMode === "signup" && "Register"}
                {authMode === "forgot" && "Send Reset Link"}
              </button>
            </form>

            <div className="text-center mt-6 pt-4 border-t border-slate-800 flex justify-center gap-4 text-xs font-medium">
              {authMode === "forgot" ? (
                <button 
                  type="button"
                  onClick={() => switchMode("login")}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  Back to Sign In
                </button>
              ) : (
                <>
                  <button 
                    type="button"
                    onClick={() => switchMode(authMode === "login" ? "signup" : "login")}
                    className="text-violet-400 hover:text-violet-300 transition-colors"
                  >
                    {authMode === "login" ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
