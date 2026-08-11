"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { dispatchApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

function socColor(soc: number) {
  if (soc > 40) return "text-emerald-400";
  if (soc > 20) return "text-amber-400";
  return "text-red-400";
}

export default function DispatchPage() {
  const qc = useQueryClient();

  const { data: recommendations = [], isLoading } = useQuery({
    queryKey: ["dispatch-recommendations"],
    queryFn: () => dispatchApi.getRecommendations().then((r) => r.data),
  });

  const acknowledge = useMutation({
    mutationFn: (id: string) => dispatchApi.acknowledge(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dispatch-recommendations"] }),
  });

  const activeRecs = recommendations.filter((r: any) => !r.was_acted_upon);
  const pastRecs = recommendations.filter((r: any) => r.was_acted_upon);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dispatch Intelligence</h1>
          <p className="text-sm text-slate-400 mt-1">
            Vehicles needing charging — triggered when SoC &lt; 25% and range &lt; remaining route + 10 km
          </p>
        </div>
        <Link
          href="/dispatch/config"
          className="border border-slate-700 hover:border-slate-500 text-slate-300 px-4 py-2 rounded-lg text-sm transition-colors"
        >
          Configure Thresholds
        </Link>
      </div>

      {/* Active recommendations */}
      <div>
        <h2 className="text-sm font-semibold text-amber-400 mb-3 flex items-center gap-2">
          <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
          Active Recommendations ({activeRecs.length})
        </h2>

        {isLoading && <div className="text-slate-500 text-sm">Loading...</div>}

        {!isLoading && activeRecs.length === 0 && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
            <div className="text-3xl mb-2">✓</div>
            <div className="text-slate-400 text-sm">All vehicles are adequately charged</div>
          </div>
        )}

        <div className="space-y-3">
          {activeRecs.map((rec: any) => (
            <div key={rec.id} className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-telemetry font-bold text-white text-lg">
                      {rec.vehicle_registration ?? rec.vehicle_id?.slice(0, 8)}
                    </span>
                    <span className={`font-telemetry text-xl font-bold ${socColor(rec.trigger_soc)}`}>
                      {rec.trigger_soc?.toFixed(0)}%
                    </span>
                    <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full">
                      {rec.estimated_range_km?.toFixed(0)} km range
                    </span>
                  </div>

                  {rec.recommended_station && (
                    <div className="text-sm text-slate-300 mb-1">
                      Recommended: <span className="text-white font-medium">{rec.recommended_station.name}</span>
                      {" · "}{rec.recommended_station.distance_km?.toFixed(1)} km away
                      {" · "}{rec.recommended_station.available_connectors} connectors available
                    </div>
                  )}

                  <div className="text-xs text-slate-500">
                    Triggered {formatRelativeTime(rec.recommended_at)}
                    {rec.predicted_depletion_at && (
                      <> · Depletes at {new Date(rec.predicted_depletion_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => acknowledge.mutate(rec.id)}
                    disabled={acknowledge.isPending}
                    className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Past recommendations */}
      {pastRecs.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">Past Recommendations ({pastRecs.length})</h2>
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-800">
                <tr className="text-slate-400">
                  <th className="text-left px-4 py-3 font-medium">Vehicle</th>
                  <th className="text-right px-4 py-3 font-medium">Trigger SoC</th>
                  <th className="text-left px-4 py-3 font-medium">Station</th>
                  <th className="text-left px-4 py-3 font-medium">When</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {pastRecs.slice(0, 20).map((rec: any) => (
                  <tr key={rec.id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-telemetry font-semibold text-white">
                      {rec.vehicle_registration ?? rec.vehicle_id?.slice(0, 8)}
                    </td>
                    <td className={`px-4 py-3 text-right font-telemetry font-bold ${socColor(rec.trigger_soc)}`}>
                      {rec.trigger_soc?.toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {rec.recommended_station?.name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {formatRelativeTime(rec.recommended_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
