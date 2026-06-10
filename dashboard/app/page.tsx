"use client";
import { useEffect, useState } from "react";
import { api, Report, DomainStats, TrendPoint, SourceReliability } from "@/lib/api";
import StatusBar from "@/components/StatusBar";
import ReportCard from "@/components/ReportCard";
import TrendChart from "@/components/TrendChart";
import SearchBox from "@/components/SearchBox";
import SourceTable from "@/components/SourceTable";
import { Activity, Zap, BarChart2, Search, Database, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

type Tab = "feed" | "trends" | "search" | "sources";

export default function Home() {
  const [tab, setTab] = useState<Tab>("feed");
  const [domain, setDomain] = useState<string | undefined>(undefined);
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<DomainStats[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [sources, setSources] = useState<SourceReliability[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    // Load each independently — don't let one failure block others
    api.getReports(domain)
      .then(setReports)
      .catch(e => console.error("Reports failed:", e))
      .finally(() => setLoading(false));

    api.getDomainStats()
      .then(setStats)
      .catch(e => console.error("Stats failed:", e));

    api.getTrends(7)
      .then(setTrends)
      .catch(e => console.error("Trends failed:", e));

    api.getSources()
      .then(setSources)
      .catch(e => console.error("Sources failed:", e));
}, [domain]);

  async function triggerPipeline() {
    setTriggering(true);
    try {
      await api.triggerPipeline();
      setTimeout(() => {
        api.getReports(domain).then(setReports);
        setTriggering(false);
      }, 3000);
    } catch (e) {
      console.error(e);
      setTriggering(false);
    }
  }

  const tabs: { id: Tab; label: string; icon: typeof Activity }[] = [
    { id: "feed", label: "Intelligence Feed", icon: Activity },
    { id: "trends", label: "Trends", icon: BarChart2 },
    { id: "search", label: "Semantic Search", icon: Search },
    { id: "sources", label: "Sources", icon: Database },
  ];

  return (
    <div className="min-h-screen bg-[#080810] text-white">
      {/* Top bar */}
      <StatusBar />

      {/* Header */}
      <header className="border-b border-white/5 bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
              <Zap size={16} className="text-violet-400" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">Signal</h1>
              <p className="text-xs text-white/30">Autonomous market intelligence · AI/ML + Fintech</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Domain filter */}
            <div className="flex rounded-lg border border-white/10 overflow-hidden text-xs">
              {[
                { value: undefined, label: "All" },
                { value: "ai_ml", label: "AI/ML" },
                { value: "fintech", label: "Fintech" },
              ].map(({ value, label }) => (
                <button
                  key={label}
                  onClick={() => setDomain(value)}
                  className={cn(
                    "px-3 py-1.5 transition-colors",
                    domain === value
                      ? "bg-violet-600 text-white"
                      : "text-white/40 hover:text-white/70 hover:bg-white/5"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Run pipeline */}
            <button
              onClick={triggerPipeline}
              disabled={triggering}
              className="flex items-center gap-2 px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white/60 hover:text-white/80 transition-all disabled:opacity-40"
            >
              <RefreshCw size={12} className={triggering ? "animate-spin" : ""} />
              {triggering ? "Running..." : "Run pipeline"}
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="max-w-7xl mx-auto px-6 pb-3 flex gap-6">
          {stats.map(s => (
            <div key={s.domain} className="flex items-center gap-3">
              <div className={cn(
                "w-2 h-2 rounded-full",
                s.domain === "ai_ml" ? "bg-violet-400" : "bg-cyan-400"
              )} />
              <span className="text-xs text-white/40">
                {s.domain === "ai_ml" ? "AI/ML" : "Fintech"}
              </span>
              <span className="text-xs font-mono text-white/60">
                {s.total_signals.toLocaleString()} signals
              </span>
              <span className="text-xs text-white/20">
                {s.total_sources} sources
              </span>
            </div>
          ))}
        </div>
      </header>

      {/* Nav tabs */}
      <div className="border-b border-white/5 bg-black/10">
        <div className="max-w-7xl mx-auto px-6 flex gap-1">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm border-b-2 transition-colors",
                tab === id
                  ? "border-violet-500 text-white"
                  : "border-transparent text-white/30 hover:text-white/60"
              )}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-white/30 text-sm gap-2">
            <RefreshCw size={14} className="animate-spin" />
            Loading...
          </div>
        ) : (
          <>
            {/* Feed */}
            {tab === "feed" && (
              <div>
                <p className="text-xs text-white/30 mb-4">
                  {reports.length} intelligence reports · latest first
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {reports.map(r => (
                    <ReportCard key={r.id} report={r} />
                  ))}
                </div>
                {reports.length === 0 && (
                  <div className="text-center py-20 text-white/20 text-sm">
                    No reports yet. Click "Run pipeline" to generate intelligence reports.
                  </div>
                )}
              </div>
            )}

            {/* Trends */}
            {tab === "trends" && (
              <div className="space-y-6">
                <div className="border border-white/8 bg-white/[0.02] rounded-xl p-6">
                  <h2 className="text-sm font-medium text-white/70 mb-1">Signal Volume — Last 7 Days</h2>
                  <p className="text-xs text-white/30 mb-4">Signals ingested per day by domain and type</p>
                  <TrendChart data={trends} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {stats.map(s => (
                    <div key={s.domain} className="border border-white/8 bg-white/[0.02] rounded-xl p-5">
                      <div className={cn(
                        "text-xs font-medium mb-3",
                        s.domain === "ai_ml" ? "text-violet-400" : "text-cyan-400"
                      )}>
                        {s.domain === "ai_ml" ? "AI/ML" : "Fintech"}
                      </div>
                      <div className="text-3xl font-mono font-bold text-white/80 mb-1">
                        {s.total_signals.toLocaleString()}
                      </div>
                      <div className="text-xs text-white/30">signals from {s.total_sources} sources</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Search */}
            {tab === "search" && (
              <div className="max-w-2xl">
                <p className="text-xs text-white/30 mb-4">
                  Semantic search powered by Qdrant vector embeddings
                </p>
                <SearchBox />
              </div>
            )}

            {/* Sources */}
            {tab === "sources" && (
              <div className="border border-white/8 bg-white/[0.02] rounded-xl p-6">
                <h2 className="text-sm font-medium text-white/70 mb-1">Source Reliability</h2>
                <p className="text-xs text-white/30 mb-4">
                  Scored by summary depth and publishing consistency
                </p>
                <SourceTable sources={sources} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}