"use client";
import { useState } from "react";
import { api, SearchResult } from "@/lib/api";
import { Search, Loader2 } from "lucide-react";
import { cn, sentimentBg, domainColor, formatDate } from "@/lib/utils";

export default function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.search(query, undefined, 5);
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Search reports by meaning... e.g. 'AI regulation Europe'"
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-4 py-2.5 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-violet-500/50 transition-colors"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 rounded-lg text-sm text-white font-medium transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          Search
        </button>
      </div>

      {/* Results */}
      {searched && results.length === 0 && !loading && (
        <p className="text-white/30 text-sm text-center py-4">No results found</p>
      )}

      <div className="space-y-3">
        {results.map((r, i) => (
          <div key={i} className="border border-white/8 bg-white/[0.02] rounded-lg p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex gap-2">
                <span className={cn("text-xs px-2 py-0.5 rounded-full border", domainColor(r.domain))}>
                  {r.domain === "ai_ml" ? "AI/ML" : "Fintech"}
                </span>
                <span className={cn("text-xs px-2 py-0.5 rounded-full border", sentimentBg(r.sentiment))}>
                  {r.sentiment}
                </span>
              </div>
              <span className="text-xs font-mono text-violet-400 shrink-0">
                {(r.score * 100).toFixed(0)}% match
              </span>
            </div>
            <h4 className="text-white/80 text-sm font-medium mb-1">{r.title}</h4>
            <p className="text-white/40 text-xs leading-relaxed mb-2">{r.summary}</p>
            <div className="flex flex-wrap gap-1">
              {r.key_themes.slice(0, 3).map((t, j) => (
                <span key={j} className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-white/30">
                  {t}
                </span>
              ))}
            </div>
            <p className="text-xs text-white/20 mt-2">{formatDate(r.generated_at)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}