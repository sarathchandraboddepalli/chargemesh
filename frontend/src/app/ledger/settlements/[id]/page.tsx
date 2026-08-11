"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ledgerApi } from "@/lib/api";

export default function SettlementReportPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data: report, isLoading } = useQuery({
    queryKey: ["settlement-report", id],
    queryFn: () => ledgerApi.getReport(id).then((r) => r.data),
    enabled: !!id,
  });

  const approve = useMutation({
    mutationFn: () => ledgerApi.approveReport(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settlement-report", id] }),
  });

  if (isLoading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!report) return <div className="p-6 text-slate-400">Report not found.</div>;

  const isPending = report.status === "pending_approval";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/ledger" className="hover:text-white">Ledger</Link>
        <span>/</span>
        <Link href="/ledger/settlements" className="hover:text-white">Settlements</Link>
        <span>/</span>
        <span className="text-white font-telemetry">{report.billing_period}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">
            Settlement Report — <span className="font-telemetry">{report.billing_period}</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {report.fleet_org_name} → {report.baas_vendor_name}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-sm px-3 py-1 rounded-full font-medium capitalize ${
            report.status === "approved" ? "bg-emerald-500/20 text-emerald-400"
            : report.status === "pending_approval" ? "bg-amber-500/20 text-amber-400"
            : "bg-slate-700 text-slate-400"
          }`}>
            {report.status?.replace(/_/g, " ")}
          </span>
          {isPending && (
            <button
              onClick={() => approve.mutate()}
              disabled={approve.isPending}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
            >
              {approve.isPending ? "Approving..." : "Approve & Settle"}
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total kWh Consumed", value: report.total_kwh_consumed?.toFixed(2) + " kWh", color: "text-blue-400" },
          { label: "Total Swaps", value: report.total_swaps, color: "text-white" },
          { label: "kWh Cost", value: `₹${report.total_kwh_cost_inr?.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`, color: "text-white" },
          { label: "Total Payable", value: `₹${report.total_amount_inr?.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`, color: "text-emerald-400" },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Breakdown */}
      {report.line_items && report.line_items.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold">Line Items ({report.line_items.length} swaps)</h3>
          </div>
          <table className="w-full text-sm">
            <thead className="border-b border-slate-800">
              <tr className="text-slate-400">
                <th className="text-left px-4 py-3 font-medium">Battery</th>
                <th className="text-left px-4 py-3 font-medium">Vehicle</th>
                <th className="text-right px-4 py-3 font-medium">kWh</th>
                <th className="text-right px-4 py-3 font-medium">kWh Cost</th>
                <th className="text-right px-4 py-3 font-medium">Deg. Cost</th>
                <th className="text-right px-4 py-3 font-medium">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {report.line_items.map((item: any, i: number) => (
                <tr key={i} className="hover:bg-slate-800/50">
                  <td className="px-4 py-3 font-telemetry text-white text-xs">{item.battery_serial}</td>
                  <td className="px-4 py-3 font-telemetry text-slate-300">{item.vehicle_registration}</td>
                  <td className="px-4 py-3 text-right font-telemetry text-slate-300">{item.kwh_consumed?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-telemetry text-slate-300">₹{item.kwh_cost_inr?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-telemetry text-slate-300">
                    {item.degradation_cost_inr > 0 ? `₹${item.degradation_cost_inr?.toFixed(2)}` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-telemetry font-bold text-white">₹{item.total_amount_inr?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
