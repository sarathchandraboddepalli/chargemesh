"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ledgerApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

export default function VendorLedgerPage() {
  const { vendor_id } = useParams<{ vendor_id: string }>();

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["vendor-reports", vendor_id],
    queryFn: () => ledgerApi.getReports().then((r) =>
      // Filter by vendor
      (r.data as any[]).filter((rpt) => rpt.baas_vendor_org_id === vendor_id)
    ),
    enabled: !!vendor_id,
  });

  const totalAmount = reports.reduce((sum: number, r: any) => sum + (r.total_amount_inr ?? 0), 0);
  const totalKwh = reports.reduce((sum: number, r: any) => sum + (r.total_kwh_consumed ?? 0), 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/ledger" className="hover:text-white">Ledger</Link>
        <span>/</span>
        <span className="text-white">Vendor</span>
      </div>

      <div>
        <h1 className="text-xl font-semibold">Vendor Ledger</h1>
        <p className="text-slate-400 text-sm mt-1 font-telemetry">{vendor_id?.slice(0, 8)}</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <div className="font-telemetry text-2xl font-bold text-white">{reports.length}</div>
          <div className="text-xs text-slate-400 mt-1">Total Reports</div>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <div className="font-telemetry text-2xl font-bold text-blue-400">{totalKwh.toFixed(1)} kWh</div>
          <div className="text-xs text-slate-400 mt-1">Total Energy</div>
        </div>
        <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <div className="font-telemetry text-2xl font-bold text-emerald-400">
            ₹{totalAmount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-slate-400 mt-1">Total Billed</div>
        </div>
      </div>

      {/* Reports list */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-800">
            <tr className="text-slate-400">
              <th className="text-left px-4 py-3 font-medium">Period</th>
              <th className="text-left px-4 py-3 font-medium">Fleet</th>
              <th className="text-right px-4 py-3 font-medium">Swaps</th>
              <th className="text-right px-4 py-3 font-medium">Amount</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">Loading...</td>
              </tr>
            )}
            {!isLoading && reports.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">No reports</td>
              </tr>
            )}
            {reports.map((r: any) => (
              <tr key={r.id} className="hover:bg-slate-800/50">
                <td className="px-4 py-3 font-telemetry text-white">{r.billing_period}</td>
                <td className="px-4 py-3 text-slate-300">{r.fleet_org_name}</td>
                <td className="px-4 py-3 text-right font-telemetry text-slate-300">{r.total_swaps}</td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-white">
                  ₹{r.total_amount_inr?.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    r.status === "approved" ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
                  }`}>
                    {r.status?.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Link href={`/ledger/settlements/${r.id}`} className="text-blue-400 text-xs">View →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
