"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { fleetApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

function socColor(soc: number | null) {
  if (soc == null) return "text-slate-400";
  if (soc > 40) return "text-emerald-400";
  if (soc > 20) return "text-amber-400";
  return "text-red-400";
}

export default function FleetPage() {
  const [search, setSearch] = useState("");

  const { data: vehicles = [], isLoading } = useQuery({
    queryKey: ["fleet-vehicles"],
    queryFn: () => fleetApi.getVehicles().then((r) => r.data),
  });

  const filtered = vehicles.filter((v: any) =>
    v.registration_number.toLowerCase().includes(search.toLowerCase()) ||
    v.model?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Fleet Management</h1>
          <p className="text-sm text-slate-400 mt-1">{vehicles.length} vehicles registered</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/fleet/import"
            className="border border-slate-700 hover:border-slate-500 text-slate-300 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Import CSV
          </Link>
          <Link
            href="/fleet/new"
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Add Vehicle
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by registration number or model..."
          className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Registration</th>
              <th className="text-left px-4 py-3 font-medium">Model</th>
              <th className="text-left px-4 py-3 font-medium">OEM</th>
              <th className="text-right px-4 py-3 font-medium">SoC</th>
              <th className="text-right px-4 py-3 font-medium">Range</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Last Update</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">Loading fleet...</td>
              </tr>
            )}
            {!isLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">No vehicles found</td>
              </tr>
            )}
            {filtered.map((v: any) => (
              <tr key={v.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3">
                  <span className="font-telemetry font-semibold text-white">{v.registration_number}</span>
                </td>
                <td className="px-4 py-3 text-slate-300">{v.model ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400 capitalize">{v.oem_slug ?? "—"}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-telemetry font-bold ${socColor(v.current_soc)}`}>
                    {v.current_soc != null ? `${v.current_soc.toFixed(1)}%` : "—"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {v.estimated_range_km != null ? `${v.estimated_range_km.toFixed(0)} km` : "—"}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                    v.status === "active" ? "bg-emerald-500/20 text-emerald-400"
                    : v.status === "charging" ? "bg-blue-500/20 text-blue-400"
                    : v.status === "idle" ? "bg-slate-700 text-slate-400"
                    : "bg-slate-700 text-slate-400"
                  }`}>
                    {v.status ?? "unknown"}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {v.last_telemetry_at ? formatRelativeTime(v.last_telemetry_at) : "Never"}
                  {v.is_stale && <span className="ml-1 text-amber-400">(stale)</span>}
                </td>
                <td className="px-4 py-3">
                  <Link
                    href={`/fleet/${v.id}`}
                    className="text-blue-400 hover:text-blue-300 text-xs"
                  >
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
