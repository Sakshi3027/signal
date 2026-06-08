"use client";
import { Report } from "@/lib/api";
import { cn, formatDate, sentimentBg, domainColor, scoreColor } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

export default function ReportCard({ report }: { report: Report }) {
  const [expanded, setExpanded] = useState(false);

  const SentimentIcon =
    report.sentiment === "bullish" ? TrendingUp :
    report.sentiment === "bearish" ? TrendingDown : Minus;

  return (
    <div className="group border border-white/8 bg-white/[0.03] hover:bg-white/[0.06] rounded-xl p-5 transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn("text-xs px-2 py-0.5 rounded-full border", domainColor(report.domain))}>
            {report.domain === "ai_ml" ? "AI/ML" : "Fintech"}
          </span>
          <span className={cn("text-xs px-2 py-0.5 rounded-full border flex items-center gap-1", sentimentBg(report.sentiment))}>
            <SentimentIcon size={10} />
            {report.sentiment}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={cn("text-sm font-mono font-semibold", scoreColor(report.quality_score))}>
            {(report.quality_score * 100).toFixed(0)}
          </span>
          <span className="text-xs text-white/20">score</span>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-white/90 font-medium text-sm leading-snug mb-2">
        {report.title}
      </h3>

      {/* Summary */}
      <p className="text-white/50 text-xs leading-relaxed mb-3">
        {report.summary}
      </p>

      {/* Themes */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {report.key_themes.slice(0, 4).map((theme, i) => (
          <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-white/5 text-white/40 border border-white/8">
            {theme}
          </span>
        ))}
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition-colors"
      >
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {expanded ? "Less" : "Notable signals"}
      </button>

      {expanded && (
        <div className="mt-3 space-y-1.5 border-t border-white/5 pt-3">
          {report.notable_signals.slice(0, 5).map((signal, i) => (
            <div key={i} className="flex gap-2 text-xs text-white/50">
              <span className="text-white/20 shrink-0">→</span>
              <span>{signal}</span>
            </div>
          ))}
          <p className="text-xs text-white/20 mt-2 italic">
            {report.quality_feedback}
          </p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
        <span className="text-xs text-white/20">run: {report.run_id}</span>
        <span className="text-xs text-white/20">{formatDate(report.generated_at)}</span>
      </div>
    </div>
  );
}