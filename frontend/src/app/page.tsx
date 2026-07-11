import Link from "next/link";
import { Mic, CheckCircle2, Shield, BarChart3, ChevronRight, MessageCircle } from "lucide-react";

export default function Home() {
  return (
    <div className="relative isolate px-6 pt-14 lg:px-8">
      {/* Hero Section */}
      <div className="mx-auto max-w-4xl py-20 sm:py-28 lg:py-36 text-center">
        <div className="mb-6 flex justify-center">
          <div className="relative rounded-full px-3 py-1 text-xs leading-6 text-slate-400 ring-1 ring-slate-800 hover:ring-slate-700 bg-slate-900/60 backdrop-blur-md flex items-center gap-1">
            <span className="text-emerald-500 font-medium">● Secure Processing Active</span>
            <span className="h-4 w-[1px] bg-slate-800 mx-2" />
            <Link href="/privacy" className="font-semibold text-violet-400 hover:text-violet-300">
              Read DPDP Privacy Disclosure <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        </div>
        
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl bg-gradient-to-b from-white via-slate-100 to-slate-400 bg-clip-text text-transparent animate-float">
          Master English Accent & Pronunciation
        </h1>
        <p className="mt-6 text-lg leading-8 text-slate-400 max-w-2xl mx-auto">
          Record or upload English audio between 30 and 45 seconds. Receive detailed breakdowns of word clarity, phoneme mistakes, and acoustic fluency scores powered by Whisper & advanced LLM feedback.
        </p>
        
        <div className="mt-10 flex items-center justify-center gap-x-6">
          <Link
            href="/upload"
            className="rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600 transition-all duration-300 transform hover:scale-[1.02] flex items-center gap-2"
          >
            <Mic className="w-4 h-4" />
            <span>Analyze Your Pronunciation</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
          <Link href="/privacy" className="text-sm font-semibold leading-6 text-slate-300 hover:text-white transition-colors">
            Learn how we protect data <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>

      {/* Feature Section */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 pb-24">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-semibold leading-7 text-violet-400 uppercase tracking-widest">How It Works</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-100 sm:text-4xl">
            Clean Architecture, Secure Processing
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-4">
            
            {/* Card 1 */}
            <div className="flex flex-col glass-panel p-6 rounded-xl relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-500 to-indigo-500" />
              <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-slate-200">
                <Mic className="h-5 w-5 flex-none text-violet-500" />
                Upload & Validate
              </dt>
              <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-400">
                <p className="flex-auto text-sm">
                  We check file integrity, duration (30-45s), microphone energy, and background noise thresholds to ensure clean assessments.
                </p>
              </dd>
            </div>

            {/* Card 2 */}
            <div className="flex flex-col glass-panel p-6 rounded-xl relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-500 to-indigo-500" />
              <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-slate-200">
                <BarChart3 className="h-5 w-5 flex-none text-violet-500" />
                Phoneme Alignment
              </dt>
              <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-400">
                <p className="flex-auto text-sm">
                  Speech is converted to words, which are translated into phonetic CMUdict symbols using Grapheme-to-Phoneme comparison models.
                </p>
              </dd>
            </div>

            {/* Card 3 */}
            <div className="flex flex-col glass-panel p-6 rounded-xl relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-500 to-indigo-500" />
              <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-slate-200">
                <MessageCircle className="h-5 w-5 flex-none text-violet-500" />
                Acoustic Diagnostics
              </dt>
              <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-400">
                <p className="flex-auto text-sm">
                  Get precise scores on Fluency, Speech pacing, Rhythm (durational variances), stress timings, and silent intervals.
                </p>
              </dd>
            </div>

            {/* Card 4 */}
            <div className="flex flex-col glass-panel p-6 rounded-xl relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-emerald-500 to-teal-500" />
              <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-slate-200">
                <Shield className="h-5 w-5 flex-none text-emerald-500" />
                DPDP Compliant
              </dt>
              <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-400">
                <p className="flex-auto text-sm">
                  In compliance with DPDP 2023, your voice files are immediately deleted upon processing. We only retain database scoring metadata.
                </p>
              </dd>
            </div>

          </dl>
        </div>
      </div>
    </div>
  );
}
