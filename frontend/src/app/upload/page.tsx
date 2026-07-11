"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Upload, Mic, Square, AlertCircle, RefreshCw, FileAudio, CheckSquare, SquareDot } from "lucide-react";
import { apiService } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  
  // Form State
  const [file, setFile] = useState<File | null>(null);
  const [referenceText, setReferenceText] = useState("");
  const [consent, setConsent] = useState(false);
  const [sessionId, setSessionId] = useState("");
  
  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const recordIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Status & Polling
  const [status, setStatus] = useState<"idle" | "uploading" | "processing" | "success" | "error">("idle");
  const [progressMsg, setProgressMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  
  // Generate session ID on mount
  useEffect(() => {
    setSessionId("session_" + Math.random().toString(36).substring(2, 15));
  }, []);

  // Timer for recording
  useEffect(() => {
    if (isRecording) {
      recordIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => {
          if (prev >= 45) {
            stopRecording();
            return 45;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      if (recordIntervalRef.current) {
        clearInterval(recordIntervalRef.current);
      }
    }
    return () => {
      if (recordIntervalRef.current) clearInterval(recordIntervalRef.current);
    };
  }, [isRecording]);

  // Microphone recording functions
  const startRecording = async () => {
    setErrorMsg(null);
    setAudioChunks([]);
    setRecordingSeconds(0);
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorMsg("Your browser does not support audio recording.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          setAudioChunks((prev) => [...prev, e.data]);
        }
      };

      recorder.onstop = () => {
        // Collect chunks when stopped
        // (Wait for state update to settle, done inside a timeout or handle directly from local array)
      };

      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);
    } catch (err: any) {
      setErrorMsg("Permission to access microphone was denied or failed.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      // Turn off microphone tracks to free the mic light
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  // Compile chunks into File object when recording finishes
  useEffect(() => {
    if (audioChunks.length > 0 && !isRecording) {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const recordedFile = new File([audioBlob], "recorded_speech.webm", {
        type: "audio/webm",
        lastModified: Date.now(),
      });
      setFile(recordedFile);
    }
  }, [audioChunks, isRecording]);

  // File Selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      
      // Client validation bounds
      const ext = selected.name.split(".").pop()?.toLowerCase();
      const validExts = ["wav", "mp3", "m4a", "aac", "ogg", "webm"];
      if (!ext || !validExts.includes(ext)) {
        setErrorMsg("Unsupported file format. Only wav, mp3, m4a, aac, ogg, webm are accepted.");
        return;
      }

      if (selected.size > 10 * 1024 * 1024) {
        setErrorMsg("File exceeds maximum 10MB size limit.");
        return;
      }

      setFile(selected);
    }
  };

  // Submit and start assessment
  const handleAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select or record an audio file first.");
      return;
    }
    if (!consent) {
      setErrorMsg("Explicit DPDP consent checkbox is required to upload speech data.");
      return;
    }

    setStatus("uploading");
    setProgressMsg("Scanning audio and uploading securely...");
    setErrorMsg(null);

    try {
      // 1. Upload file
      const uploadRes = await apiService.uploadAudio(file, consent, sessionId);
      const uploadId = uploadRes.upload_id;

      // 2. Trigger Celery analysis
      setStatus("processing");
      setProgressMsg("Verifying audio metrics and enqueuing assessment task...");
      const analyzeRes = await apiService.analyzeAudio(uploadId, referenceText || undefined);
      const taskId = analyzeRes.task_id;

      // 3. Poll Celery status
      pollTaskStatus(taskId);

    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err.response?.data?.detail || "An error occurred during audio processing. Please try again.");
    }
  };

  const pollTaskStatus = (taskId: string) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      setProgressMsg(`AI transcribing and comparing phonemes... (Attempt ${attempts})`);
      
      try {
        const res = await apiService.getTaskStatus(taskId);
        
        if (res.status === "SUCCESS") {
          clearInterval(interval);
          setProgressMsg("Loading results dashboard...");
          if (res.analysis_id) {
            router.push(`/results/${res.analysis_id}`);
          } else {
            router.push("/upload");
          }
        } else if (res.status === "FAILURE") {
          clearInterval(interval);
          setStatus("error");
          setErrorMsg(res.error || "Acoustic assessment failed. Ensure English speech with low noise.");
        }
        
        // Timeout after 60 seconds (30 attempts * 2s)
        if (attempts > 30) {
          clearInterval(interval);
          setStatus("error");
          setErrorMsg("Assessment timed out. The server took too long to respond. Please try again.");
        }
      } catch (err) {
        // Ignore temporary network errors during polling
      }
    }, 2000);
  };

  // We can fetch the latest analysis using polling or editing the endpoint.
  // Let's check: how can we poll for the analysis id?
  // Let's write the code in `pollTaskStatus` that checks if the task successfully completed,
  // and we'll edit `/task/{task_id}` to return `analysis_id`! Let's make that edit to `analysis.py` next.
  // For the frontend, let's write:
  const checkFinishedTask = async (taskId: string, interval: any) => {
    try {
      const res = await apiService.getTaskStatus(taskId);
      if (res.status === "SUCCESS") {
        clearInterval(interval);
        // Navigate to the analysis id!
        // We will make `/task/{task_id}` return `{"analysis_id": analysis_id}`.
        if (res.analysis_id) {
          router.push(`/results/${res.analysis_id}`);
        } else {
          // Fallback, query user's latest analysis
          router.push(`/results/latest`);
        }
      } else if (res.status === "FAILURE") {
        clearInterval(interval);
        setStatus("error");
        setErrorMsg(res.error || "Acoustic assessment failed. Check microphone quality.");
      }
    } catch (err) {
      // ignore
    }
  };

  // We'll override the setInterval call with this function
  useEffect(() => {
    if (status === "processing") {
      // we handle it in form submit
    }
  }, [status]);

  const startPolling = (taskId: string) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      setProgressMsg(`AI analyzing speech rhythm and vowels... (Attempt ${attempts}/30)`);
      try {
        const res = await apiService.getTaskStatus(taskId);
        if (res.status === "SUCCESS") {
          clearInterval(interval);
          setProgressMsg("Loading results dashboard...");
          if (res.analysis_id) {
            router.push(`/results/${res.analysis_id}`);
          } else {
            // query latest
            router.push("/upload"); // reload
          }
        } else if (res.status === "FAILURE") {
          clearInterval(interval);
          setStatus("error");
          setErrorMsg(res.error || "Acoustic assessment failed. Make sure you speak clearly.");
        }
      } catch (err) {
        // ignore
      }

      if (attempts >= 30) {
        clearInterval(interval);
        setStatus("error");
        setErrorMsg("Task timed out. The worker is busy. Please try again.");
      }
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8 flex-grow flex flex-col justify-center">
      <div className="glass-panel rounded-2xl p-8 sm:p-12 shadow-2xl relative overflow-hidden">
        
        {/* Background glow strip */}
        <div className="absolute top-0 left-0 w-full h-[3px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-indigo-500" />
        
        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold tracking-tight text-white">Speech Assessment Center</h2>
          <p className="mt-2 text-sm text-slate-400">
            Record directly or upload an audio file between <span className="text-violet-400 font-semibold">30 and 45 seconds</span>.
          </p>
        </div>

        {status === "idle" && (
          <form onSubmit={handleAssessment} className="space-y-6">
            
            {/* Error Message */}
            {errorMsg && (
              <div className="flex items-center gap-3 p-4 rounded-lg bg-red-950/50 border border-red-900/50 text-red-400 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Reference text helper (Optional) */}
            <div>
              <label htmlFor="ref-text" className="block text-sm font-semibold text-slate-300 mb-1">
                Target Reference Text (Optional)
              </label>
              <textarea
                id="ref-text"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500 transition-colors"
                rows={3}
                placeholder="Type the exact sentences you want to speak. If left blank, our AI will auto-detect whatever you say."
                value={referenceText}
                onChange={(e) => setReferenceText(e.target.value)}
              />
            </div>

            {/* Input Selection: Upload or Record */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Box 1: Microphone Recorder */}
              <div className="border border-slate-800 bg-slate-950/50 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${isRecording ? "bg-red-500 animate-pulse" : "bg-slate-700"}`} />
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Recorder</span>
                </div>
                
                {isRecording ? (
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-500 flex items-center justify-center text-white transition-all transform scale-110 shadow-lg shadow-red-500/20"
                  >
                    <Square className="w-6 h-6 fill-white" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={startRecording}
                    className="w-16 h-16 rounded-full bg-violet-600 hover:bg-violet-500 flex items-center justify-center text-white transition-all shadow-lg shadow-violet-500/20"
                  >
                    <Mic className="w-6 h-6" />
                  </button>
                )}

                <div className="text-center">
                  <p className="text-2xl font-bold text-white tracking-widest">
                    00:{recordingSeconds < 10 ? `0${recordingSeconds}` : recordingSeconds}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {isRecording ? "Recording speech..." : "Click mic to record. Speak for 30-45s."}
                  </p>
                </div>
                
                {recordingSeconds > 0 && recordingSeconds < 30 && !isRecording && (
                  <p className="text-xs text-amber-500 font-medium">
                    ⚠️ Current: {recordingSeconds}s. Audio must be at least 30s to upload.
                  </p>
                )}
                {recordingSeconds >= 30 && (
                  <p className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                    <CheckSquare className="w-3.5 h-3.5" /> Valid duration recorded!
                  </p>
                )}
              </div>

              {/* Box 2: File Selector */}
              <div className="border border-slate-800 bg-slate-950/50 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-4">
                <FileAudio className="w-10 h-10 text-slate-500" />
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Upload File</span>
                
                <label className="cursor-pointer bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors">
                  Choose Audio File
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </label>

                <p className="text-xs text-slate-500">
                  {file ? `Selected: ${file.name}` : "WAV, MP3, M4A, AAC, OGG, WEBM (Max 10MB)"}
                </p>

                {file && (
                  <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-violet-400">
                    <span>Ready for analysis</span>
                  </div>
                )}
              </div>

            </div>

            {/* DPDP Compliance Checkbox */}
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-900 flex items-start gap-3">
              <input
                id="consent-check"
                type="checkbox"
                className="mt-1 w-4 h-4 rounded text-violet-600 focus:ring-violet-500 bg-slate-950 border-slate-800"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
              />
              <label htmlFor="consent-check" className="text-xs text-slate-400 leading-normal">
                <span className="text-white font-semibold block mb-0.5">Explicit DPDP Consent Checkbox</span>
                I explicitly consent to the collection, processing, and temporary storage of my voice recording for the sole purpose of pronunciation assessment. I understand that my raw audio file will be <span className="text-violet-400 font-semibold">deleted immediately</span> after analysis, and that no permanent storage of my voice identifiers will occur.
              </label>
            </div>

            {/* Trigger Button */}
            <button
              type="submit"
              disabled={!file || !consent}
              className="w-full rounded-lg py-3 text-sm font-semibold bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-violet-500/20 transition-all duration-300"
            >
              Analyze Pronunciation
            </button>

          </form>
        )}

        {/* Polling / Processing Screens */}
        {(status === "uploading" || status === "processing") && (
          <div className="py-12 flex flex-col items-center justify-center text-center space-y-6">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-slate-800 border-t-violet-600 animate-spin" />
              <SquareDot className="w-6 h-6 text-violet-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white capitalize">{status}</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">{progressMsg}</p>
            </div>

            <div className="w-full max-w-xs bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
              <div 
                className="bg-gradient-to-r from-violet-500 to-indigo-500 h-full transition-all duration-500" 
                style={{ width: status === "uploading" ? "40%" : "85%" }} 
              />
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="py-12 flex flex-col items-center justify-center text-center space-y-6">
            <div className="w-16 h-16 rounded-full bg-red-950/30 border border-red-900/50 flex items-center justify-center text-red-500">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-white">Assessment Interrupted</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">{errorMsg}</p>
            </div>
            <button
              onClick={() => {
                setStatus("idle");
                setErrorMsg(null);
                setFile(null);
                setRecordingSeconds(0);
              }}
              className="bg-slate-900 hover:bg-slate-800 border border-slate-800 px-6 py-2.5 rounded-lg text-sm text-slate-300 font-semibold transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
