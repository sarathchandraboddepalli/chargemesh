"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: session, isLoading } = useQuery({
    queryKey: ["session", id],
    queryFn: () => sessionsApi.get(id).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!session) return <div className="p-6 text-slate-400">Session not found.</div>;

  const duration = session.started_at && session.ended_at
    ? Math.round((new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 60000)
    : null;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/sessions" className="hover:text-white">Sessions</Link>
        <span>/</span>
        <span className="text-white font-telemetry">{session.id?.slice(0, 8)}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold font-telemetry">{session.vehicle_registration ?? "Session"}</h1>
          <p className="text-slate-400 text-sm mt-1">{session.station_name} — {session.network_name}</p>
        </div>
        <span className={`text-sm px-3 py-1 rounded-full font-medium capitalize ${
          session.status === "completed" ? "bg-emerald-500/20 text-emerald-400"
          : session.status === "active" ? "bg-blue-500/20 text-blue-400"
          : session.status === "failed" ? "bg-red-500/20 text-red-400"
          : "bg-slate-700 text-slate-400"
        }`}>
          {session.status}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Energy Delivered", value: session.energy_delivered_kwh != null ? `${session.energy_delivered_kwh.toFixed(2)} kWh` : "—", color: "text-blue-400" },
          { label: "Total Cost", value: session.total_cost_inr != null ? `₹${session.total_cost_inr.toFixed(2)}` : "—", color: "text-white" },
          { label: "Duration", value: duration != null ? `${duration} min` : "—", color: "text-white" },
          { label: "Booking Type", value: session.booking_type, color: "text-slate-300" },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color} capitalize`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold mb-4">Session Details</h3>
        <dl className="grid grid-cols-3 gap-4 text-sm">
          {[
            ["Vehicle ID", session.vehicle_id?.slice(0, 8)],
            ["Station", session.station_name],
            ["Network", session.network_name],
            ["Connector ID", session.connector_id ?? "—"],
            ["External Session ID", session.external_session_id ?? "—"],
            ["Started", session.started_at ? new Date(session.started_at).toLocaleString("en-IN") : "—"],
            ["Ended", session.ended_at ? new Date(session.ended_at).toLocaleString("en-IN") : "—"],
            ["SoC Start", session.soc_start_pct != null ? `${session.soc_start_pct}%` : "—"],
            ["SoC End", session.soc_end_pct != null ? `${session.soc_end_pct}%` : "—"],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-slate-400">{label}</dt>
              <dd className="text-white font-telemetry mt-0.5">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
