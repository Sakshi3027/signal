import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function sentimentColor(sentiment: string): string {
  switch (sentiment) {
    case "bullish": return "text-emerald-400";
    case "bearish": return "text-red-400";
    default: return "text-yellow-400";
  }
}

export function sentimentBg(sentiment: string): string {
  switch (sentiment) {
    case "bullish": return "bg-emerald-400/10 text-emerald-400 border-emerald-400/20";
    case "bearish": return "bg-red-400/10 text-red-400 border-red-400/20";
    default: return "bg-yellow-400/10 text-yellow-400 border-yellow-400/20";
  }
}

export function domainColor(domain: string): string {
  return domain === "ai_ml"
    ? "bg-violet-400/10 text-violet-400 border-violet-400/20"
    : "bg-cyan-400/10 text-cyan-400 border-cyan-400/20";
}

export function scoreColor(score: number): string {
  if (score >= 0.8) return "text-emerald-400";
  if (score >= 0.6) return "text-yellow-400";
  return "text-red-400";
}