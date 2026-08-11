"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { stationsApi } from "@/lib/api";

export default function StationsPage() {
  const [search, setSearch] = useState("");

  const { data: stations = [], isLoading } = useQuery({
    queryKey: ["stations"],
    queryFn: () => stationsApi.getAll().then((r) => r.data),
  });

  const filtered = stations.filter((s: any) =>
    s.name?.toLowerCase().includes(search.toLowerCase()) ||
    s.city?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Charging Stations</h1>
          <p className="text-sm text-slate-400 mt-1">{stations.length} stations across connected networks</p>
        </div>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by station name or city..."
          className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {isLoading && (
          <div className="col-span-3 text-center text-slate-500 py-8">Loading stations...</div>
        )}
        {filtered.map((station: any) => {
          const avail = station.available_connectors ?? 0;
          const total = station.total_connectors ?? 0;
          const pct = total ? Math.round((avail / total) * 100) : 0;
          return (
            <Link key={station.id} href={`/stations/${station.id}`}
              className="bg-slate-900 rounded-xl border border-slate-800 p-4 hover:border-slate-600 transition-colors block">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-semibold text-white">{station.name}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{station.city} · {station.network_name}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  station.is_operational ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                }`}>
                  {station.is_operational ? "Online" : "Offline"}
                </span>
              </div>

              {/* Availability bar */}
              <div className="mb-3">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Availability</span>
                  <span className="font-telemetry">{avail}/{total} connectors</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${pct > 50 ? "bg-emerald-500" : pct > 0 ? "bg-amber-500" : "bg-red-500"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-400">
                {station.price_per_kwh_inr && (
                  <span className="font-telemetry text-white">
                    ₹{station.price_per_kwh_inr}/kWh
                  </span>
                )}
                {station.connector_types?.map((ct: string) => (
                  <span key={ct} className="bg-slate-800 px-2 py-0.5 rounded text-slate-300">{ct}</span>
                ))}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
