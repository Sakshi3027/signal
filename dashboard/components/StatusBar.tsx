"use client";
import { useEffect, useState } from "react";
import { api, HealthStatus } from "@/lib/api";
import { Activity, Database, Search, Layers } from "lucide-react";

export default function StatusBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(console.error);
    const interval = setInterval(() => {
      api.getHealth().then(setHealth).catch(console.error);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const items = [
    { label: "PostgreSQL", ok: health.postgres, icon: Database },
    { label: "Qdrant", ok: health.qdrant, icon: Search },
    { label: "DuckDB", ok: health.duckdb, icon: Layers },
  ];

  return (
    <div className="border-b border-white/5 bg-black/40 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 py-2 flex items-center justify-between">
        <div className="flex items-center gap-6">
          {items.map(({ label, ok, icon: Icon }) => (
            <div key={label} className="flex items-center gap-1.5 text-xs">
              <div className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
              <Icon size={12} className="text-white/40" />
              <span className="text-white/50">{label}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 text-xs text-white/40">
          <span>{health.total_signals.toLocaleString()} signals</span>
          <span>{health.total_reports} reports</span>
          <div className="flex items-center gap-1">
            <Activity size={10} className={health.status === "ok" ? "text-emerald-400" : "text-red-400"} />
            <span className={health.status === "ok" ? "text-emerald-400" : "text-red-400"}>
              {health.status}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}