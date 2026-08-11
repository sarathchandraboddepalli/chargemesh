"use client";

import { useQuery } from "@tanstack/react-query";
import { fleetApi, thermalApi, dispatchApi } from "@/lib/api";
import { formatSoC, socBgColor, formatRelativeTime } from "@/lib/formatters";
import dynamic from "next/dynamic";

// Lazy-load map to avoid SSR issues with Mapbox
const FleetLiveMap = dynamic(() => import("@/components/map/FleetLiveMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-900 rounded-xl flex items-center justify-center text-slate-500">
      Loading map...
    </div>
  ),
});

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["fleet-summary"],
    queryFn: () => fleetApi.getSummary().then((r) => r.data),
  });

  const { data: vehicles } = useQuery({
    queryKey: ["fleet-vehicles"],
    queryFn: () => fleetApi.getVehicles().then((r) => r.data),
  });

  const { data: thermalAlerts } = useQuery({
    queryKey: ["thermal-alerts"],
    queryFn: () => thermalApi.getActiveAlerts().then((r) => r.data),
  });

  const { data: recommendations } = useQuery({
    queryKey: ["dispatch-recommendations"],
    queryFn: () => dispatchApi.getRecommendations().then((r) => r.data),
  });

  const socBuckets = summary?.soc_distribution ?? {};

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Fleet Operations Center</h1>
          <p className="text-sm text-slate-400">
            Live view — updates every 60s
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-sm text-slate-400">Live</span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-5 gap-4 px-6 py-4 border-b border-slate-800">
        {[
          { label: "Total Vehicles", value: summary?.total_vehicles ?? "—", color: "text-white" },
          { label: "Active", value: summary?.active_vehicles ?? "—", color: "text-emerald-400" },
          { label: "Charging", value: summary?.charging_vehicles ?? "—", color: "text-blue-400" },
          { label: "At Risk (SoC<25%)", value: summary?.at_risk_vehicles ?? "—", color: "text-red-400" },
          { label: "Thermal Alerts", value: thermalAlerts?.length ?? "—", color: "text-amber-400" },
        ].map((stat) => (
          <div key={stat.label} className="bg-slate-900 rounded-lg p-4">
            <div className={`font-telemetry text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Main content: Map + Sidebar */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        {/* Map */}
        <div className="flex-1 bg-slate-900 rounded-xl overflow-hidden">
          <FleetLiveMap vehicles={vehicles ?? []} />
        </div>

        {/* Right sidebar */}
        <div className="w-80 flex flex-col gap-4 overflow-auto">
          {/* SoC Distribution */}
          <div className="bg-slate-900 rounded-xl p-4">
            <h3 className="text-sm font-semibold mb-3">SoC Distribution</h3>
            {Object.entries(socBuckets).map(([bucket, count]) => {
              const total = summary?.total_vehicles ?? 1;
              const pct = Math.round(((count as number) / total) * 100);
              const colors: Record<string, string> = {
                "0-20": "bg-red-500",
                "20-40": "bg-amber-500",
                "40-60": "bg-yellow-500",
                "60-80": "bg-emerald-500",
                "80-100": "bg-blue-500",
              };
              return (
                <div key={bucket} className="mb-2">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>{bucket}%</span>
                    <span className="font-telemetry">{count as number} vehicles</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${colors[bucket] ?? "bg-slate-500"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Dispatch Recommendations */}
          <div className="bg-slate-900 rounded-xl p-4 flex-1 overflow-auto">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-amber-400 rounded-full" />
              Dispatch Alerts
              {recommendations?.length > 0 && (
                <span className="bg-amber-500/20 text-amber-400 text-xs px-2 py-0.5 rounded-full ml-auto">
                  {recommendations.length}
                </span>
              )}
            </h3>
            {recommendations?.length === 0 && (
              <p className="text-slate-500 text-sm">No active recommendations</p>
            )}
            {(recommendations ?? []).slice(0, 5).map((rec: any) => (
              <div key={rec.id} className="mb-3 p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-telemetry text-sm font-semibold text-white">
                    {rec.vehicle_registration ?? rec.vehicle_id.slice(0, 8)}
                  </span>
                  <span className="font-telemetry text-xs text-red-400">
                    {rec.trigger_soc?.toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  → {rec.station_name ?? "Nearest available station"}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {formatRelativeTime(rec.recommended_at)}
                </p>
              </div>
            ))}
          </div>

          {/* Thermal Alerts */}
          {(thermalAlerts ?? []).length > 0 && (
            <div className="bg-slate-900 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <span className="text-red-400">🌡</span> Thermal Alerts
              </h3>
              {(thermalAlerts ?? []).slice(0, 3).map((alert: any) => (
                <div
                  key={alert.id}
                  className={`mb-2 p-3 rounded-lg border text-xs ${
                    alert.severity === "critical"
                      ? "bg-red-500/10 border-red-500/30 text-red-300"
                      : "bg-amber-500/10 border-amber-500/30 text-amber-300"
                  }`}
                >
                  <div className="font-semibold capitalize">{alert.severity}: {alert.alert_type.replace(/_/g, " ")}</div>
                  <div className="font-telemetry mt-1">{alert.temperature_celsius?.toFixed(1)}°C</div>
                  <div className="text-slate-400 mt-1">{formatRelativeTime(alert.created_at)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
