import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to inject bearer token
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface WordScore {
  word: string;
  start_time: number;
  end_time: number;
  score: number;
  is_mispronounced: boolean;
  is_unclear: boolean;
  phonemes_expected: string | null;
  phonemes_actual: string | null;
}

export interface DetailFeedback {
  word: string;
  issue: string;
  correct_pronunciation: string;
  suggestion: string;
  difficulty_level: string;
}

export interface ScoreBreakdown {
  stress_score: number;
  rhythm_score: number;
  pauses_score: number;
  timing_score: number;
  intonation_score: number;
  phoneme_similarity_score: number;
}

export interface AnalysisResponse {
  id: string;
  upload_id: string;
  overall_score: number;
  fluency_score: number;
  accuracy_score: number;
  completeness_score: number;
  confidence_score: number;
  suggestions: string;
  created_at: string;
  scores: ScoreBreakdown;
  word_scores: WordScore[];
  feedback: DetailFeedback[];
}

export const apiService = {
  // Auth
  async register(email: string, password_raw: string) {
    const res = await api.post("/api/v1/auth/register", { email, password: password_raw });
    return res.data;
  },

  async login(email: string, password_raw: string) {
    // Form data login
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password_raw);
    const res = await api.post("/api/v1/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return res.data;
  },

  async forgotPassword(email: string) {
    const res = await api.post("/api/v1/auth/forgot-password", { email });
    return res.data;
  },

  // Upload
  async uploadAudio(file: File, consent: boolean, sessionId: string) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("consent", String(consent));
    formData.append("session_id", sessionId);
    formData.append("purpose", "pronunciation_assessment");
    
    const res = await api.post("/api/v1/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  // Analyze
  async analyzeAudio(uploadId: string, referenceText?: string) {
    const res = await api.post("/api/v1/analyze", {
      upload_id: uploadId,
      reference_text: referenceText || null,
    });
    return res.data;
  },

  async getTaskStatus(taskId: string) {
    const res = await api.get(`/api/v1/task/${taskId}`);
    return res.data;
  },

  // Analysis Result
  async getAnalysis(analysisId: string): Promise<AnalysisResponse> {
    const res = await api.get(`/api/v1/analysis/${analysisId}`);
    return res.data;
  },

  async deleteAnalysis(analysisId: string) {
    const res = await api.delete(`/api/v1/analysis/${analysisId}`);
    return res.data;
  },

  // Feedback & Purges
  async submitFeedback(analysisId: string, rating: number, comments?: string) {
    const res = await api.post("/api/v1/feedback", {
      analysis_id: analysisId,
      rating,
      comments: comments || null,
    });
    return res.data;
  },

  async requestDataDeletion(email: string) {
    const res = await api.post("/api/v1/user/deletion-request", { email });
    return res.data;
  },
};
export default api;
