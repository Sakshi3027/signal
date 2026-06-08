"use client";
import { SourceReliability } from "@/lib/api";
import { cn, domainColor } from "@/lib/utils";

export default function SourceTable({ sources }: { sources: SourceReliability[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/5">
            <th className="text-left py-2 pr-4 text-white/30 font-normal">Source</th>
            <th className="text-left py-2 pr-4 text-white/30 font-normal">Domain</th>
            <th className="text-left py-2 pr-4 text-white/30 font-normal">Type</th>
            <th className="text-right py-2 pr-4 text-white/30 font-normal">Signals</th>
            <th className="text-right py-2 text-white/30 font-normal">Reliability</th>
          </tr>
        </thead>
        <tbody>
          {sources.slice(0, 12).map((s, i) => (
            <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
              <td className="py-2 pr-4 text-white/60 font-mono">{s.source_name}</td>
              <td className="py-2 pr-4">
                <span className={cn("px-1.5 py-0.5 rounded-full border text-xs", domainColor(s.domain))}>
                  {s.domain === "ai_ml" ? "AI/ML" : "Fintech"}
                </span>
              </td>
              <td className="py-2 pr-4 text-white/30">{s.signal_type}</td>
              <td className="py-2 pr-4 text-right text-white/60">{s.total_signals}</td>
              <td className="py-2 text-right">
                <div className="flex items-center justify-end gap-2">
                  <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-violet-400 rounded-full"
                      style={{ width: `${s.reliability_score * 100}%` }}
                    />
                  </div>
                  <span className="text-white/40 w-8 text-right">
                    {(s.reliability_score * 100).toFixed(0)}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}