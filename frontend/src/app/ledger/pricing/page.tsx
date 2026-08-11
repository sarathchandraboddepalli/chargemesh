"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ledgerApi } from "@/lib/api";

export default function PricingConfigPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    price_per_kwh_inr: 8,
    price_per_soh_point_inr: 50,
    degradation_threshold_pct: 0.05,
    is_active: true,
  });

  const { data: configs = [], isLoading } = useQuery({
    queryKey: ["pricing-configs"],
    queryFn: () => ledgerApi.getPricingConfigs().then((r) => r.data),
  });

  const create = useMutation({
    mutationFn: () => ledgerApi.createPricingConfig(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pricing-configs"] });
      setShowForm(false);
    },
  });

  const update = (field: string, value: any) => setForm((f) => ({ ...f, [field]: value }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/ledger" className="hover:text-white">Ledger</Link>
        <span>/</span>
        <span className="text-white">Pricing Config</span>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">BaaS Pricing Configuration</h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure pricing between fleet operators and battery swap vendors
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Config
        </button>
      </div>

      {/* New config form */}
      {showForm && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <h3 className="text-sm font-semibold mb-4">New Pricing Agreement</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Price per kWh (₹)</label>
              <input type="number" step="0.5" value={form.price_per_kwh_inr}
                onChange={(e) => update("price_per_kwh_inr", Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Sun Mobility: ₹8 · Local: ₹9</p>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Price per SoH Point (₹)</label>
              <input type="number" step="1" value={form.price_per_soh_point_inr}
                onChange={(e) => update("price_per_soh_point_inr", Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Charged when excess degradation occurs</p>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Degradation Threshold (%/100kWh)</label>
              <input type="number" step="0.001" value={form.degradation_threshold_pct}
                onChange={(e) => update("degradation_threshold_pct", Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
              <p className="text-xs text-slate-500 mt-1">Normal degradation threshold</p>
            </div>
          </div>

          <div className="bg-slate-950 rounded-lg p-3 text-xs font-telemetry text-slate-400 mb-4">
            Formula: total = (kWh × ₹{form.price_per_kwh_inr}) + max(0, actual_deg - threshold × kWh/100) × ₹{form.price_per_soh_point_inr}
          </div>

          <div className="flex gap-3">
            <button onClick={() => create.mutate()} disabled={create.isPending}
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              {create.isPending ? "Creating..." : "Create Config"}
            </button>
            <button onClick={() => setShowForm(false)}
              className="border border-slate-700 text-slate-400 px-4 py-2 rounded-lg text-sm transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Existing configs */}
      <div className="space-y-3">
        {isLoading && <div className="text-slate-500 text-sm">Loading...</div>}
        {configs.map((c: any) => (
          <div key={c.id} className={`bg-slate-900 rounded-xl border p-4 ${c.is_active ? "border-slate-700" : "border-slate-800 opacity-60"}`}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-semibold text-white">
                  {c.fleet_org_name} ↔ {c.baas_vendor_name}
                </div>
                <div className="text-xs text-slate-400 mt-0.5">Config ID: {c.id?.slice(0, 8)}</div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${c.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"}`}>
                {c.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <div className="text-slate-400">Price/kWh</div>
                <div className="font-telemetry text-white font-semibold">₹{c.price_per_kwh_inr}</div>
              </div>
              <div>
                <div className="text-slate-400">Price/SoH Point</div>
                <div className="font-telemetry text-white font-semibold">₹{c.price_per_soh_point_inr}</div>
              </div>
              <div>
                <div className="text-slate-400">Deg. Threshold</div>
                <div className="font-telemetry text-white font-semibold">{c.degradation_threshold_pct}%</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
