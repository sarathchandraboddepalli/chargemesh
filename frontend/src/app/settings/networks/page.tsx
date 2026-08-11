"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Network {
  id: string;
  name: string;
  slug: string;
  integration_type: string;
  is_active: boolean;
  last_synced_at: string | null;
  station_count: number;
}

export default function NetworkSettingsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: networks = [], isLoading } = useQuery({
    queryKey: ["networks"],
    queryFn: () => api.get("/networks/").then((r) => r.data),
  });

  const sync = useMutation({
    mutationFn: (id: string) => api.post(`/networks/${id}/sync`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["networks"] }),
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Charging Networks</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage connected charging network integrations
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + Connect Network
        </button>
      </div>

      {/* Network cards */}
      <div className="grid grid-cols-2 gap-4">
        {isLoading && (
          <div className="col-span-2 text-slate-500 text-sm">Loading networks...</div>
        )}
        {networks.map((network: Network) => (
          <div key={network.id} className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-semibold text-white">{network.name}</div>
                <div className="text-xs text-slate-400 mt-0.5 capitalize">
                  {network.integration_type.replace(/_/g, " ")} · {network.slug}
                </div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                network.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"
              }`}>
                {network.is_active ? "Active" : "Inactive"}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{network.station_count} stations</span>
              {network.last_synced_at && (
                <span>Synced {new Date(network.last_synced_at).toLocaleString("en-IN")}</span>
              )}
            </div>

            <div className="mt-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => sync.mutate(network.id)}
                disabled={sync.isPending}
                className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50 transition-colors"
              >
                {sync.isPending ? "Syncing..." : "Sync Now"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Mock data notice */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
        <div className="text-sm font-semibold text-amber-400 mb-1">Mock Mode Active</div>
        <p className="text-xs text-slate-400">
          ChargeMesh is running with <span className="font-telemetry text-amber-300">CHARGING_NETWORK_MODE=mock</span>.
          ChargeZone (3 stations) and Statiq (2 stations) are simulated.
          Set <span className="font-telemetry text-amber-300">CHARGING_NETWORK_MODE=live</span> and configure real API keys to go live.
        </p>
      </div>
    </div>
  );
}
