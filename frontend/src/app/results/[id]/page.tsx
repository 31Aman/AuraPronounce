"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, Download, Trash2, RotateCw, AlertTriangle, ShieldCheck, 
  HelpCircle, Star, Sparkles, BookOpen, Volume2, Award
} from "lucide-react";
import { apiService, AnalysisResponse } from "@/lib/api";

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalysisResponse | null>(null);
  
  // Rating states for assessment feedback
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackComments, setFeedbackComments] = useState("");

  // Fetch results on load
  useEffect(() => {
    if (id) {
      fetchResults();
    }
  }, [id]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const res = await apiService.getAnalysis(id);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load pronunciation report.");
    } finally {
      setLoading(false);
    }
  };

  // Delete this analysis
  const handleDelete = async () => {
    if (confirm("Are you sure you want to permanently delete this report? This will wipe the database metadata and is non-reversible (Right to Erasure compliance).")) {
      try {
        await apiService.deleteAnalysis(id);
        alert("Report deleted successfully.");
        router.push("/upload");
      } catch (err) {
        alert("Failed to delete report.");
      }
    }
  };

  // Submit Feedback
  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return;
    try {
      await apiService.submitFeedback(id, rating, feedbackComments);
      setFeedbackSubmitted(true);
    } catch (err) {
      alert("Failed to submit rating.");
    }
  };

  if (loading) {
    return (
      <div className="flex-grow flex flex-col items-center justify-center py-24 space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-slate-800 border-t-violet-600 animate-spin" />
        <p className="text-slate-400 text-sm">Retrieving your analysis report...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-grow flex flex-col items-center justify-center py-24 space-y-6 max-w-md mx-auto text-center px-4">
        <div className="w-16 h-16 rounded-full bg-red-950/30 border border-red-900/50 flex items-center justify-center text-red-500">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-white">Report Unavailable</h3>
          <p className="text-sm text-slate-400">{error || "Ensure the ID is correct and has not been deleted."}</p>
        </div>
        <Link href="/upload" className="bg-slate-900 border border-slate-800 px-6 py-2 rounded-lg text-sm text-slate-300 font-semibold transition-colors">
          Go back
        </Link>
      </div>
    );
  }

  // Helper to color code scores
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
    if (score >= 65) return "text-amber-400 border-amber-500/20 bg-amber-500/10";
    return "text-red-400 border-red-500/20 bg-red-500/10";
  };

  // Helper for word heatmap styles
  const getWordStyle = (score: number) => {
    if (score >= 80) return "bg-emerald-950/20 text-emerald-400 border-emerald-900/50 hover:bg-emerald-900/30";
    if (score >= 65) return "bg-amber-950/20 text-amber-400 border-amber-900/50 hover:bg-amber-900/30";
    return "bg-red-950/20 text-red-400 border-red-900/50 hover:bg-red-900/30";
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 flex-grow space-y-8 print:py-0">
      
      {/* Top action row */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6 print:hidden">
        <Link href="/upload" className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Assessment</span>
        </Link>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => window.print()}
            className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Download PDF</span>
          </button>
          <button 
            onClick={handleDelete}
            className="flex items-center gap-2 bg-red-950/40 border border-red-900/50 px-4 py-2 rounded-lg text-sm text-red-400 hover:bg-red-900/30 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Wipe Record</span>
          </button>
          <Link 
            href="/upload" 
            className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-2 rounded-lg text-sm text-white hover:from-violet-500 hover:to-indigo-500 transition-all"
          >
            <RotateCw className="w-4 h-4" />
            <span>Try Again</span>
          </Link>
        </div>
      </div>

      {/* Grid: Circle Score & Primary Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Circular Score Dashboard */}
        <div className="glass-panel rounded-2xl p-8 flex flex-col items-center justify-center text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
          
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-6">Overall Performance</span>
          
          {/* Circular Graph */}
          <div className="relative w-44 h-44 flex items-center justify-center">
            {/* SVG circle meter */}
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="88"
                cy="88"
                r="76"
                strokeWidth="10"
                stroke="rgba(30, 41, 59, 0.5)"
                fill="transparent"
              />
              <circle
                cx="88"
                cy="88"
                r="76"
                strokeWidth="10"
                stroke="url(#purpleGlow)"
                strokeDasharray={2 * Math.PI * 76}
                strokeDashoffset={2 * Math.PI * 76 * (1 - data.overall_score / 100)}
                strokeLinecap="round"
                fill="transparent"
              />
              <defs>
                <linearGradient id="purpleGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#4f46e5" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-5xl font-extrabold text-white tracking-tight">{Math.round(data.overall_score)}</span>
              <span className="text-xs font-medium text-slate-400 mt-1">/ 100</span>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-2 gap-4 w-full border-t border-slate-800 pt-6">
            <div className="text-center">
              <span className="text-xs text-slate-500 block">Accuracy</span>
              <span className="text-lg font-bold text-violet-400">{Math.round(data.accuracy_score)}%</span>
            </div>
            <div className="text-center">
              <span className="text-xs text-slate-500 block">Fluency</span>
              <span className="text-lg font-bold text-indigo-400">{Math.round(data.fluency_score)}%</span>
            </div>
          </div>
        </div>

        {/* Right Col: Detailed Acoustic Breakdown */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-8 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
          
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4 block">Acoustic Engine Analysis</span>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
            {/* Metric 1 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Stress Placements</span>
                <span className="text-slate-400 font-bold">{data.scores.stress_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-violet-500 h-full rounded-full" style={{ width: `${data.scores.stress_score}%` }} />
              </div>
            </div>

            {/* Metric 2 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Speech Rhythm</span>
                <span className="text-slate-400 font-bold">{data.scores.rhythm_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${data.scores.rhythm_score}%` }} />
              </div>
            </div>

            {/* Metric 3 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Unnecessary Pauses</span>
                <span className="text-slate-400 font-bold">{data.scores.pauses_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-violet-400 h-full rounded-full" style={{ width: `${data.scores.pauses_score}%` }} />
              </div>
            </div>

            {/* Metric 4 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Syllable Timing</span>
                <span className="text-slate-400 font-bold">{data.scores.timing_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-indigo-400 h-full rounded-full" style={{ width: `${data.scores.timing_score}%` }} />
              </div>
            </div>

            {/* Metric 5 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Intonation Pitch</span>
                <span className="text-slate-400 font-bold">{data.scores.intonation_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-fuchsia-500 h-full rounded-full" style={{ width: `${data.scores.intonation_score}%` }} />
              </div>
            </div>

            {/* Metric 6 */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Phoneme Similarity</span>
                <span className="text-slate-400 font-bold">{data.scores.phoneme_similarity_score}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${data.scores.phoneme_similarity_score}%` }} />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 mt-6 p-3 rounded bg-slate-950/60 border border-slate-900 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>Scoring engine measures relative durational standard deviations (rhythm) and Whisper logprobs.</span>
          </div>
        </div>

      </div>

      {/* Heatmap: Highlighted Word Transcript */}
      <div className="glass-panel rounded-2xl p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
        
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-violet-500" />
              <span>Pronunciation Heatmap</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">Hover over words to inspect expected vs. actual phonemic spelling.</p>
          </div>
          
          {/* Legend */}
          <div className="flex gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/20 border border-emerald-500/40" /> Good
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/20 border border-amber-500/40" /> Unclear
            </span>
            <span className="flex items-center gap-1.5 text-red-400">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/40" /> Mistake
            </span>
          </div>
        </div>

        {/* Word Heatmap Wrap */}
        <div className="flex flex-wrap gap-x-2.5 gap-y-3.5 p-5 bg-slate-950 rounded-xl border border-slate-900 leading-loose">
          {data.word_scores.map((w, idx) => (
            <div
              key={idx}
              className={`px-2.5 py-1 rounded border text-sm font-medium transition-all cursor-help relative group ${getWordStyle(w.score)}`}
            >
              {w.word}
              
              {/* Tooltip on hover showing phoneme mismatch */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-max bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-300 shadow-2xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-20 flex flex-col gap-0.5 min-w-[120px]">
                <span className="font-bold text-white text-[10px] uppercase tracking-wider text-slate-500">Phonemes</span>
                <span>Expected: <span className="font-mono text-violet-400">/{w.phonemes_expected || "N/A"}/</span></span>
                <span>Actual: <span className="font-mono text-indigo-400">/{w.phonemes_actual || "N/A"}/</span></span>
                <span className="border-t border-slate-800 mt-1 pt-0.5 text-[10px] text-slate-400 font-semibold">Score: {Math.round(w.score)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid: Mistakes table & suggestions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Mistakes Table Breakdown (2 cols) */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-8 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
          
          <div className="mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-violet-500" />
              <span>Identified Pronunciation Mistakes</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">Specific sound alterations and articulation advice.</p>
          </div>

          {data.feedback.length > 0 ? (
            <div className="overflow-x-auto w-full">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="py-2.5">Word</th>
                    <th className="py-2.5">Acoustic Issue</th>
                    <th className="py-2.5">Articulation Fix</th>
                    <th className="py-2.5">Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-slate-300">
                  {data.feedback.map((f, idx) => (
                    <tr key={idx} className="hover:bg-slate-950/40">
                      <td className="py-3 font-bold text-white">{f.word}</td>
                      <td className="py-3 text-red-400 font-medium">{f.issue}</td>
                      <td className="py-3 max-w-sm text-slate-400 leading-relaxed">{f.suggestion}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400 font-semibold">
                          {f.difficulty_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500">
              No major phonetic mistakes detected. Your vowel and consonant sound shapes are highly accurate!
            </div>
          )}
          
          <div className="mt-6 border-t border-slate-900 pt-4 text-[10px] text-slate-500">
            Forced alignment parses audio against dictionary phone files to highlight exact articulation shifts.
          </div>
        </div>

        {/* AI Recommendations & Suggestions (1 col) */}
        <div className="glass-panel rounded-2xl p-8 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
          
          <div className="mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-violet-500" />
              <span>AI Coaching Feedback</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">Global evaluations and custom speech training recommendations.</p>
          </div>

          <div className="bg-slate-950/70 border border-slate-900 rounded-xl p-5 leading-relaxed text-sm text-slate-300 relative">
            <span className="text-violet-400 font-bold block mb-2 text-xs uppercase tracking-wider">Pronunciation Coach</span>
            "{data.suggestions}"
          </div>

          <div className="mt-6 border-t border-slate-900 pt-6 space-y-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest block">Practice Exercises</span>
            <div className="flex gap-3 text-xs leading-normal">
              <BookOpen className="w-4 h-4 text-violet-500 flex-shrink-0 mt-0.5" />
              <p className="text-slate-400">
                Practice dental fricatives (e.g. TH) by saying "three, thin, leather, thought" daily.
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* Client Feedback Rating Box */}
      <div className="glass-panel rounded-2xl p-8 relative overflow-hidden print:hidden">
        <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500" />
        
        <h3 className="text-lg font-bold text-white mb-2">Help Us Improve Our AI Models</h3>
        <p className="text-xs text-slate-500 mb-6">How accurate was this pronunciation evaluation? Submit your satisfaction score.</p>
        
        {feedbackSubmitted ? (
          <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/50 text-emerald-400 text-sm">
            Thank you! Your feedback has been securely logged to our training metrics audit repository.
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-4">
            <div className="flex items-center gap-1.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  type="button"
                  key={star}
                  className="transition-transform hover:scale-115 focus:outline-none"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                >
                  <Star 
                    className={`w-8 h-8 ${
                      star <= (hoverRating || rating) 
                        ? "text-amber-500 fill-amber-500" 
                        : "text-slate-700"
                    }`} 
                  />
                </button>
              ))}
            </div>
            
            <div className="max-w-md space-y-3">
              <input
                type="text"
                placeholder="Optional comments (e.g., specific mistakes missed, volume issues)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500"
                value={feedbackComments}
                onChange={(e) => setFeedbackComments(e.target.value)}
              />
              <button
                type="submit"
                disabled={rating === 0}
                className="bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-xs px-4 py-2 rounded-lg transition-colors"
              >
                Submit Feedback
              </button>
            </div>
          </form>
        )}
      </div>

    </div>
  );
}
