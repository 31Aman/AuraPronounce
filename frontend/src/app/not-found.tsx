import Link from "next/link";
import { MessageSquareCode, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex-grow flex flex-col items-center justify-center py-24 text-center px-4">
      <div className="relative mb-6">
        <MessageSquareCode className="w-16 h-16 text-slate-700 animate-pulse" />
        <span className="absolute -bottom-2 -right-2 bg-violet-600 text-white font-extrabold text-xs px-2 py-0.5 rounded-full">
          404
        </span>
      </div>
      
      <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">Page Not Found</h2>
      <p className="mt-2 text-sm text-slate-400 max-w-sm mx-auto">
        The assessment reports or pages you requested might have been deleted for privacy compliance or do not exist.
      </p>
      
      <div className="mt-8">
        <Link 
          href="/" 
          className="bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-3 rounded-lg text-sm text-white font-semibold hover:from-violet-500 hover:to-indigo-500 transition-all flex items-center gap-2"
        >
          <Home className="w-4 h-4" />
          <span>Return Home</span>
        </Link>
      </div>
    </div>
  );
}
