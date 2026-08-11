"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface OEMAdapter {
  id: string;
  oem_slug: string;
  display_name: string;
  connection_status: string;
  last_polled_at: string | null;
  vehicle_count: number;
  is_active: boolean;
}

export default function OEMSettingsPage() {
  const qc = useQueryClient();

  const { data: adapters = [], isLoading } = useQuery({
    queryKey: ["oem-adapters"],
    queryFn: () => api.get("/oems/").then((r) => r.data),
  });

  const test = useMutation({
    mutationFn: (id: string) => api.post(`/oems/${id}/test`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["oem-adapters"] }),
  });

  const STATUS_COLORS: Record<string, string> = {
    connected: "bg-emerald-500/20 text-emerald-400",
    disconnected: "bg-red-500/20 text-red-400",
    error: "bg-red-500/20 text-red-400",
    pending: "bg-amber-500/20 text-amber-400",
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">OEM Adapters</h1>
        <p className="text-sm text-slate-400 mt-1">
          Telemetry integrations with EV manufacturers
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {isLoading && <div className="col-span-2 text-slate-500 text-sm">Loading...</div>}
        {adapters.map((adapter: OEMAdapter) => (
          <div key={adapter.id} className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-semibold text-white">{adapter.display_name}</div>
                <div className="text-xs text-slate-400 mt-0.5 font-telemetry">{adapter.oem_slug}</div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[adapter.connection_status] ?? "bg-slate-700 text-slate-400"}`}>
                {adapter.connection_status}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
              <span>{adapter.vehicle_count} vehicles</span>
              {adapter.last_polled_at && (
                <span>Last polled: {new Date(adapter.last_polled_at).toLocaleTimeString("en-IN")}</span>
              )}
            </div>

            <div className="border-t border-slate-800 pt-3">
              <button
                onClick={() => test.mutate(adapter.id)}
                disabled={test.isPending}
                className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50 transition-colors"
              >
                Test Connection
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Mock mode notice */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
        <div className="text-sm font-semibold text-amber-400 mb-1">Mock OEM Mode Active</div>
        <p className="text-xs text-slate-400">
          <span className="font-telemetry text-amber-300">OEM_MODE=mock</span> — Ola S1 Pro, Ather 450X, and TVS iQube telemetry is simulated.
        </p>
        <ul className="mt-2 text-xs text-slate-400 space-y-1">
          <li>• <span className="font-telemetry">MH02AB1234</span> — low SoC critical scenario (drops to 18%)</li>
          <li>• <span className="font-telemetry">KA01AB5678</span> — thermal spike scenario (46°C during fast charge)</li>
          <li>• <span className="font-telemetry">MH02CD9012</span> — battery swap scenario</li>
        </ul>
      </div>
    </div>
  );
}
