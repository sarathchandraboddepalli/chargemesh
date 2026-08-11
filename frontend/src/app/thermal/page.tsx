"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { thermalApi } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

const SEVERITY_COLORS = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  info: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

export default function ThermalPage() {
  const [severity, setSeverity] = useState("all");

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["thermal-alerts", severity],
    queryFn: () => thermalApi.getAlerts(severity === "all" ? undefined : severity).then((r) => r.data),
  });

  const criticalCount = alerts.filter((a: any) => a.severity === "critical").length;
  const warningCount = alerts.filter((a: any) => a.severity === "warning").length;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Thermal Intelligence</h1>
        <p className="text-sm text-slate-400 mt-1">
          Battery temperature monitoring. Baseline: 35°C. Warning ≥ 42°C. Critical ≥ 48°C.
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
          <div className="font-telemetry text-3xl font-bold text-red-400">{criticalCount}</div>
          <div className="text-xs text-slate-400 mt-1">Critical Alerts</div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
          <div className="font-telemetry text-3xl font-bold text-amber-400">{warningCount}</div>
          <div className="text-xs text-slate-400 mt-1">Warning Alerts</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="font-telemetry text-3xl font-bold text-white">{alerts.length}</div>
          <div className="text-xs text-slate-400 mt-1">Total Active</div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {["all", "critical", "warning", "info"].map((s) => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
              severity === s
                ? "bg-blue-500 text-white"
                : "bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Alert list */}
      {isLoading && <div className="text-slate-500 text-sm">Loading thermal alerts...</div>}

      {!isLoading && alerts.length === 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center">
          <div className="text-3xl mb-2">✓</div>
          <div className="text-slate-400 text-sm">No thermal alerts</div>
        </div>
      )}

      <div className="space-y-3">
        {alerts.map((alert: any) => {
          const colors = SEVERITY_COLORS[alert.severity as keyof typeof SEVERITY_COLORS] ?? SEVERITY_COLORS.info;
          return (
            <div key={alert.id} className={`rounded-xl border p-4 ${colors}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold capitalize text-sm">
                      {alert.severity}: {alert.alert_type.replace(/_/g, " ")}
                    </span>
                    <span className="font-telemetry font-bold text-lg">
                      {alert.temperature_celsius?.toFixed(1)}°C
                    </span>
                  </div>
                  <div className="text-sm opacity-80">
                    Battery: {alert.battery_serial ?? alert.battery_id?.slice(0, 8)}
                  </div>
                  {alert.thermal_stress_accumulated != null && (
                    <div className="text-xs opacity-70 mt-1">
                      Accumulated stress: {alert.thermal_stress_accumulated.toFixed(1)} °C·h
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <Link
                    href={`/thermal/${alert.battery_id}`}
                    className="text-xs underline opacity-70 hover:opacity-100"
                  >
                    View history
                  </Link>
                  <div className="text-xs opacity-60 mt-1">{formatRelativeTime(alert.created_at)}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
