const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Report {
  id: number;
  run_id: string;
  domain: string;
  title: string;
  summary: string;
  key_themes: string[];
  notable_signals: string[];
  sentiment: "bullish" | "bearish" | "neutral";
  quality_score: number;
  quality_feedback: string;
  generated_at: string;
  created_at: string;
}

export interface SearchResult {
  domain: string;
  title: string;
  summary: string;
  key_themes: string[];
  sentiment: string;
  quality_score: number;
  generated_at: string;
  score: number;
}

export interface DomainStats {
  domain: string;
  total_signals: number;
  total_sources: number;
  latest_signal: string;
  earliest_signal: string;
}

export interface TrendPoint {
  domain: string;
  signal_type: string;
  signal_date: string;
  signal_count: number;
  source_count: number;
}

export interface SourceReliability {
  source_name: string;
  domain: string;
  signal_type: string;
  total_signals: number;
  reliability_score: number;
  last_seen: string;
}

export interface HealthStatus {
  status: string;
  postgres: boolean;
  qdrant: boolean;
  duckdb: boolean;
  total_signals: number;
  total_reports: number;
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  getHealth: () => fetchAPI<HealthStatus>("/health"),
  getReports: (domain?: string) =>
    fetchAPI<Report[]>(`/reports/${domain ? `?domain=${domain}` : ""}`),
  getReport: (id: number) => fetchAPI<Report>(`/reports/${id}`),
  getDomainStats: () => fetchAPI<DomainStats[]>("/analytics/domains"),
  getTrends: (days = 7) => fetchAPI<TrendPoint[]>(`/analytics/trends?days=${days}`),
  getSources: () => fetchAPI<SourceReliability[]>("/analytics/sources"),
  search: (query: string, domain?: string, limit = 5) =>
    fetchAPI<SearchResult[]>("/search/", {
      method: "POST",
      body: JSON.stringify({ query, domain, limit }),
    }),
  triggerPipeline: () =>
    fetchAPI("/pipeline/run", { method: "POST" }),
};