"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from "recharts";

export default function AnalyticsPage() {
  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getOverview().then((r) => r.data),
  });

  const tooltipStyle = {
    contentStyle: { background: "#1e293b", border: "1px solid #334155", borderRadius: 8 },
    labelStyle: { color: "#94a3b8", fontSize: 11 },
    itemStyle: { fontSize: 12 },
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-slate-400 mt-1">Fleet performance and energy consumption insights</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total kWh Delivered (30d)", value: analytics?.total_kwh_30d?.toFixed(0) ?? "—", suffix: " kWh", color: "text-blue-400" },
          { label: "Avg Session Duration", value: analytics?.avg_session_duration_min?.toFixed(0) ?? "—", suffix: " min", color: "text-white" },
          { label: "Dispatch Effectiveness", value: analytics?.dispatch_effectiveness_pct?.toFixed(0) ?? "—", suffix: "%", color: "text-emerald-400" },
          { label: "Avg Fleet SoC", value: analytics?.avg_fleet_soc?.toFixed(1) ?? "—", suffix: "%", color: "text-white" },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color}`}>
              {s.value}{s.value !== "—" ? s.suffix : ""}
            </div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Daily energy chart */}
      {analytics?.daily_kwh && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Daily Energy Delivered (kWh)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={analytics.daily_kwh}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis tick={{ fontSize: 10, fill: "#64748b" }} unit=" kWh" />
              <Tooltip {...tooltipStyle} itemStyle={{ ...tooltipStyle.itemStyle, color: "#3B82F6" }} />
              <Bar dataKey="kwh" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Fleet SoC trend */}
      {analytics?.soc_trend && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Fleet Average SoC Trend</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={analytics.soc_trend}>
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#64748b" }} unit="%" />
              <Tooltip {...tooltipStyle} itemStyle={{ ...tooltipStyle.itemStyle, color: "#10B981" }} />
              <Line type="monotone" dataKey="avg_soc" stroke="#10B981" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Sessions by network */}
      {analytics?.sessions_by_network && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Sessions by Charging Network</h3>
          <div className="space-y-3">
            {analytics.sessions_by_network.map((n: any) => {
              const total = analytics.sessions_by_network.reduce((sum: number, x: any) => sum + x.count, 0);
              const pct = total ? Math.round((n.count / total) * 100) : 0;
              return (
                <div key={n.network}>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>{n.network}</span>
                    <span className="font-telemetry">{n.count} sessions ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
