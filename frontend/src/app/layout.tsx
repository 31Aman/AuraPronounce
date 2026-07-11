import "./globals.css";
import Link from "next/link";
import { MessageSquareCode, ShieldCheck, HelpCircle } from "lucide-react";
import Navbar from "@/components/Navbar";

export const metadata = {
  title: "AuraPronounce - AI English Pronunciation Coach",
  description: "Upload your speech, align phonemes, and instantly improve your English pronunciation with detailed AI-driven analytics.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-[#020617] text-[#f8fafc] bg-grid-pattern antialiased selection:bg-violet-600 selection:text-white">
        
        {/* Navigation Bar */}
        <Navbar />

        {/* Main Content Area */}
        <main className="flex-grow flex flex-col relative">
          {/* Radial blur glows for premium aesthetics */}
          <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] radial-blur-glow rounded-full pointer-events-none -z-10" />
          <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[600px] h-[600px] radial-blur-glow rounded-full pointer-events-none -z-10" />
          {children}
        </main>

        {/* Footer */}
        <footer className="w-full border-t border-slate-800 bg-slate-950/90 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-500">
              &copy; 2026 AuraPronounce. Built for secure, AI-powered pronunciation learning in compliance with India's DPDP Act 2023.
            </p>
            <div className="flex space-x-6 text-xs text-slate-400">
              <Link href="/privacy" className="hover:text-white transition-colors">Privacy & Data Consent Policy</Link>
              <Link href="/privacy#data-residency" className="hover:text-white transition-colors">Data Residency</Link>
              <Link href="/privacy#deletion" className="hover:text-white transition-colors">Right to Erasure (Delete Data)</Link>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
