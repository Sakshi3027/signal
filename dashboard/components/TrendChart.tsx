"use client";
import { TrendPoint } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, CartesianGrid
} from "recharts";

interface Props { data: TrendPoint[] }

export default function TrendChart({ data }: Props) {
  // Aggregate by date + domain
  const byDate: Record<string, { date: string; ai_ml: number; fintech: number }> = {};

  for (const point of data) {
    const date = new Date(point.signal_date).toLocaleDateString("en-US", {
      month: "short", day: "numeric"
    });
    if (!byDate[date]) byDate[date] = { date, ai_ml: 0, fintech: 0 };
    if (point.domain === "ai_ml") byDate[date].ai_ml += point.signal_count;
    else byDate[date].fintech += point.signal_count;
  }

  const chartData = Object.values(byDate).slice(-7);

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-white/20 text-sm">
        No trend data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="date" tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "#0a0a0a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
          labelStyle={{ color: "rgba(255,255,255,0.6)" }}
          itemStyle={{ color: "rgba(255,255,255,0.8)" }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.4)" }} />
        <Bar dataKey="ai_ml" name="AI/ML" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
        <Bar dataKey="fintech" name="Fintech" fill="#06b6d4" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}