"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ledgerApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

function statusColor(s: string) {
  if (s === "approved") return "bg-emerald-500/20 text-emerald-400";
  if (s === "pending_approval") return "bg-amber-500/20 text-amber-400";
  if (s === "draft") return "bg-slate-700 text-slate-400";
  return "bg-slate-700 text-slate-400";
}

export default function LedgerPage() {
  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["settlement-reports"],
    queryFn: () => ledgerApi.getReports().then((r) => r.data),
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">BaaS Ledger</h1>
          <p className="text-sm text-slate-400 mt-1">
            Battery-as-a-Service settlement reports between fleet operators and vendors
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/ledger/pricing"
            className="border border-slate-700 hover:border-slate-500 text-slate-300 px-4 py-2 rounded-lg text-sm transition-colors">
            Pricing Config
          </Link>
          <Link href="/ledger/settlements"
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            All Settlements
          </Link>
        </div>
      </div>

      {/* Reports table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Period</th>
              <th className="text-left px-4 py-3 font-medium">Fleet → Vendor</th>
              <th className="text-right px-4 py-3 font-medium">Total kWh</th>
              <th className="text-right px-4 py-3 font-medium">Swaps</th>
              <th className="text-right px-4 py-3 font-medium">Amount</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Generated</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && reports.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                  No settlement reports yet. Reports are generated on the 1st of each month.
                </td>
              </tr>
            )}
            {reports.map((r: any) => (
              <tr key={r.id} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 font-telemetry text-white">{r.billing_period}</td>
                <td className="px-4 py-3 text-slate-300 text-xs">
                  {r.fleet_org_name} → {r.baas_vendor_name}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {r.total_kwh_consumed?.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                  {r.total_swaps}
                </td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-white">
                  ₹{r.total_amount_inr?.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${statusColor(r.status)}`}>
                    {r.status?.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs">
                  {formatRelativeTime(r.created_at)}
                </td>
                <td className="px-4 py-3">
                  <Link href={`/ledger/settlements/${r.id}`}
                    className="text-blue-400 hover:text-blue-300 text-xs">
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
