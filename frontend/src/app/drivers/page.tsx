"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function DriversPage() {
  const [search, setSearch] = useState("");

  const { data: drivers = [], isLoading } = useQuery({
    queryKey: ["drivers"],
    queryFn: () => api.get("/drivers/").then((r) => r.data),
  });

  const filtered = drivers.filter((d: any) =>
    d.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    d.phone?.includes(search)
  );

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Drivers</h1>
          <p className="text-sm text-slate-400 mt-1">{drivers.length} registered drivers</p>
        </div>
        <Link
          href="/drivers/new"
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Add Driver
        </Link>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or phone..."
          className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Name</th>
              <th className="text-left px-4 py-3 font-medium">Phone</th>
              <th className="text-left px-4 py-3 font-medium">Assigned Vehicle</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">No drivers found</td>
              </tr>
            )}
            {filtered.map((d: any) => (
              <tr key={d.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 text-white font-medium">{d.full_name}</td>
                <td className="px-4 py-3 font-telemetry text-slate-300">{d.phone}</td>
                <td className="px-4 py-3">
                  {d.assigned_vehicle_registration ? (
                    <Link href={`/fleet/${d.assigned_vehicle_id}`}
                      className="font-telemetry text-blue-400 hover:text-blue-300">
                      {d.assigned_vehicle_registration}
                    </Link>
                  ) : (
                    <span className="text-slate-500">Unassigned</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    d.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"
                  }`}>
                    {d.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link href={`/drivers/${d.id}`} className="text-blue-400 hover:text-blue-300 text-xs">
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
