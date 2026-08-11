"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { batteryApi } from "@/lib/api";

export default function BatteriesPage() {
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  const { data: batteries = [], isLoading } = useQuery({
    queryKey: ["batteries", flaggedOnly],
    queryFn: () => batteryApi.getAll(flaggedOnly).then((r) => r.data),
  });

  const sohColor = (soh: number | null) => {
    if (soh == null) return "text-slate-400";
    if (soh > 80) return "text-emerald-400";
    if (soh > 70) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Battery Health</h1>
          <p className="text-sm text-slate-400 mt-1">{batteries.length} batteries tracked</p>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={flaggedOnly}
            onChange={(e) => setFlaggedOnly(e.target.checked)}
            className="accent-red-400"
          />
          Flagged only
        </label>
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Serial No.</th>
              <th className="text-left px-4 py-3 font-medium">Chemistry</th>
              <th className="text-right px-4 py-3 font-medium">SoH</th>
              <th className="text-right px-4 py-3 font-medium">Cycles</th>
              <th className="text-right px-4 py-3 font-medium">Thermal Stress</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && batteries.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">No batteries found</td>
              </tr>
            )}
            {batteries.map((b: any) => (
              <tr key={b.id} className={`hover:bg-slate-800/50 transition-colors ${b.is_flagged ? "bg-red-500/5" : ""}`}>
                <td className="px-4 py-3 font-telemetry font-semibold text-white">{b.serial_number}</td>
                <td className="px-4 py-3 text-slate-300 uppercase">{b.chemistry}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-telemetry font-bold ${sohColor(b.current_soh)}`}>
                    {b.current_soh?.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {b.cycle_count?.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {b.accumulated_thermal_stress?.toFixed(1)} °C·h
                </td>
                <td className="px-4 py-3">
                  {b.is_flagged ? (
                    <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
                      Flagged
                    </span>
                  ) : (
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">
                      Healthy
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Link href={`/batteries/${b.id}`} className="text-blue-400 hover:text-blue-300 text-xs">
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
