"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ledgerApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

export default function SettlementsPage() {
  const { data: settlements = [], isLoading } = useQuery({
    queryKey: ["settlements"],
    queryFn: () => ledgerApi.getSettlements().then((r) => r.data),
  });

  return (
    <div className="p-6">
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
        <Link href="/ledger" className="hover:text-white">Ledger</Link>
        <span>/</span>
        <span className="text-white">Settlements</span>
      </div>

      <h1 className="text-xl font-semibold mb-6">Individual Swap Settlements</h1>

      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Battery</th>
              <th className="text-left px-4 py-3 font-medium">Vehicle</th>
              <th className="text-right px-4 py-3 font-medium">kWh</th>
              <th className="text-right px-4 py-3 font-medium">Degradation</th>
              <th className="text-right px-4 py-3 font-medium">kWh Cost</th>
              <th className="text-right px-4 py-3 font-medium">Deg. Cost</th>
              <th className="text-right px-4 py-3 font-medium">Total</th>
              <th className="text-left px-4 py-3 font-medium">Swap Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && settlements.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">No settlements found</td>
              </tr>
            )}
            {settlements.map((s: any) => (
              <tr key={s.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 font-telemetry text-white text-xs">{s.battery_serial}</td>
                <td className="px-4 py-3 font-telemetry text-slate-300">{s.vehicle_registration}</td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {s.kwh_consumed?.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {s.degradation_this_session?.toFixed(4)}%
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  ₹{s.kwh_cost_inr?.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {s.degradation_cost_inr > 0 ? `₹${s.degradation_cost_inr?.toFixed(2)}` : "—"}
                </td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-white">
                  ₹{s.total_amount_inr?.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {formatRelativeTime(s.swapped_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
