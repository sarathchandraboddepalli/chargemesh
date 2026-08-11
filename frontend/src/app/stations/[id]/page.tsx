"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { stationsApi, sessionsApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

export default function StationDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: station, isLoading } = useQuery({
    queryKey: ["station", id],
    queryFn: () => stationsApi.get(id).then((r) => r.data),
    enabled: !!id,
  });

  const { data: recentSessions = [] } = useQuery({
    queryKey: ["station-sessions", id],
    queryFn: () => sessionsApi.getByStation(id).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!station) return <div className="p-6 text-slate-400">Station not found.</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/stations" className="hover:text-white">Stations</Link>
        <span>/</span>
        <span className="text-white">{station.name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{station.name}</h1>
          <p className="text-slate-400 text-sm mt-1">{station.city} · {station.network_name}</p>
          <p className="text-slate-500 text-xs mt-0.5">{station.address}</p>
        </div>
        <span className={`text-sm px-3 py-1 rounded-full font-medium ${
          station.is_operational ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
        }`}>
          {station.is_operational ? "Online" : "Offline"}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Available", value: station.available_connectors, color: "text-emerald-400" },
          { label: "Total Connectors", value: station.total_connectors, color: "text-white" },
          { label: "Price/kWh", value: station.price_per_kwh_inr ? `₹${station.price_per_kwh_inr}` : "—", color: "text-white" },
          { label: "Network", value: station.network_name, color: "text-blue-400" },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Connector types */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold mb-3">Connector Types</h3>
        <div className="flex gap-2 flex-wrap">
          {station.connector_types?.map((ct: string) => (
            <span key={ct} className="bg-slate-800 border border-slate-700 px-3 py-1 rounded-lg text-sm text-slate-300">
              {ct}
            </span>
          ))}
        </div>
      </div>

      {/* Recent sessions */}
      {recentSessions.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Recent Sessions</h3>
          <div className="space-y-3">
            {recentSessions.slice(0, 10).map((s: any) => (
              <div key={s.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-telemetry text-white">{s.vehicle_registration ?? s.vehicle_id?.slice(0, 8)}</span>
                  <span className="text-slate-400 ml-2">{s.energy_delivered_kwh?.toFixed(2)} kWh</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    s.status === "completed" ? "bg-emerald-500/20 text-emerald-400"
                    : s.status === "active" ? "bg-blue-500/20 text-blue-400"
                    : "bg-slate-700 text-slate-400"
                  }`}>
                    {s.status}
                  </span>
                  <span className="text-slate-500 text-xs">{formatRelativeTime(s.started_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
