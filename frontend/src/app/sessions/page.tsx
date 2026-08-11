"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  booked: "bg-amber-500/20 text-amber-400",
  cancelled: "bg-slate-700 text-slate-400",
  failed: "bg-red-500/20 text-red-400",
};

export default function SessionsPage() {
  const [status, setStatus] = useState("all");

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ["sessions", status],
    queryFn: () =>
      sessionsApi.getAll(status === "all" ? undefined : status).then((r) => r.data),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Charging Sessions</h1>
          <p className="text-sm text-slate-400 mt-1">{sessions.length} sessions</p>
        </div>
      </div>

      {/* Status filter */}
      <div className="flex gap-2 mb-4">
        {["all", "active", "booked", "completed", "failed"].map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
              status === s
                ? "bg-blue-500 text-white"
                : "bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Vehicle</th>
              <th className="text-left px-4 py-3 font-medium">Station</th>
              <th className="text-left px-4 py-3 font-medium">Type</th>
              <th className="text-right px-4 py-3 font-medium">Energy</th>
              <th className="text-right px-4 py-3 font-medium">Cost</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Started</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && sessions.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">No sessions found</td>
              </tr>
            )}
            {sessions.map((s: any) => (
              <tr key={s.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 font-telemetry font-semibold text-white">
                  {s.vehicle_registration ?? s.vehicle_id?.slice(0, 8)}
                </td>
                <td className="px-4 py-3 text-slate-300">{s.station_name ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300 capitalize">
                    {s.booking_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {s.energy_delivered_kwh != null ? `${s.energy_delivered_kwh.toFixed(2)} kWh` : "—"}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-white">
                  {s.total_cost_inr != null ? `₹${s.total_cost_inr.toFixed(2)}` : "—"}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_COLORS[s.status] ?? "bg-slate-700 text-slate-400"}`}>
                    {s.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {s.started_at ? formatRelativeTime(s.started_at) : "—"}
                </td>
                <td className="px-4 py-3">
                  <Link href={`/sessions/${s.id}`} className="text-blue-400 hover:text-blue-300 text-xs">
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
