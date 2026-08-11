"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { batteryApi } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { formatRelativeTime } from "@/lib/formatters";

export default function BatteryDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: battery, isLoading } = useQuery({
    queryKey: ["battery", id],
    queryFn: () => batteryApi.get(id).then((r) => r.data),
    enabled: !!id,
  });

  const { data: thermalHistory = [] } = useQuery({
    queryKey: ["battery-thermal", id],
    queryFn: () => batteryApi.getThermalHistory(id).then((r) => r.data),
    enabled: !!id,
  });

  const { data: swapHistory = [] } = useQuery({
    queryKey: ["battery-swaps", id],
    queryFn: () => batteryApi.getSwaps(id).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!battery) return <div className="p-6 text-slate-400">Battery not found.</div>;

  const sohColor = battery.current_soh > 80 ? "text-emerald-400" : battery.current_soh > 70 ? "text-amber-400" : "text-red-400";

  const thermalChartData = thermalHistory.slice(-100).map((r: any) => ({
    time: new Date(r.recorded_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    temp: r.battery_temp_celsius,
  }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/batteries" className="hover:text-white">Batteries</Link>
        <span>/</span>
        <span className="text-white font-telemetry">{battery.serial_number}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold font-telemetry">{battery.serial_number}</h1>
          <p className="text-slate-400 text-sm mt-1">
            {battery.chemistry?.toUpperCase()} · {battery.capacity_kwh} kWh ·{" "}
            {battery.manufacturer ?? "Unknown OEM"}
          </p>
        </div>
        {battery.is_flagged && (
          <span className="bg-red-500/20 text-red-400 border border-red-500/30 px-3 py-1 rounded-full text-sm font-medium">
            Flagged for Inspection
          </span>
        )}
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "State of Health", value: `${battery.current_soh?.toFixed(2)}%`, color: sohColor },
          { label: "Cycle Count", value: battery.cycle_count?.toLocaleString(), color: "text-white" },
          { label: "Thermal Stress", value: `${battery.accumulated_thermal_stress?.toFixed(1)} °C·h`, color: battery.accumulated_thermal_stress > 150 ? "text-amber-400" : "text-white" },
          { label: "Projected RUL", value: battery.projected_rul_cycles ? `${battery.projected_rul_cycles} cycles` : "—", color: "text-slate-300" },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* SoH gauge (visual bar) */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold mb-3">State of Health</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1 h-4 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                battery.current_soh > 80 ? "bg-emerald-500"
                : battery.current_soh > 70 ? "bg-amber-500"
                : "bg-red-500"
              }`}
              style={{ width: `${Math.min(100, battery.current_soh)}%` }}
            />
          </div>
          <span className={`font-telemetry text-xl font-bold ${sohColor}`}>
            {battery.current_soh?.toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>0%</span>
          <span className="text-amber-500">⚠ 70%</span>
          <span className="text-emerald-500">100%</span>
        </div>
      </div>

      {/* Thermal history chart */}
      {thermalChartData.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-3">Thermal History</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={thermalChartData}>
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis domain={[20, 60]} tick={{ fontSize: 10, fill: "#64748b" }} unit="°C" />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                itemStyle={{ color: "#F59E0B", fontSize: 12 }}
              />
              <ReferenceLine y={42} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: "Warning 42°C", fill: "#F59E0B", fontSize: 10 }} />
              <ReferenceLine y={48} stroke="#EF4444" strokeDasharray="4 4" label={{ value: "Critical 48°C", fill: "#EF4444", fontSize: 10 }} />
              <Line type="monotone" dataKey="temp" stroke="#F59E0B" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Swap history */}
      {swapHistory.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Swap History ({swapHistory.length})</h3>
          <div className="space-y-3">
            {swapHistory.slice(0, 10).map((s: any) => (
              <div key={s.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-telemetry text-white">{s.vehicle_registration}</span>
                  <span className="text-slate-400 ml-2">
                    SoH: {s.soh_before_pct?.toFixed(1)}% → {s.soh_after_pct?.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    s.settlement_status === "settled" ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-amber-500/20 text-amber-400"
                  }`}>
                    {s.settlement_status}
                  </span>
                  <span className="text-slate-500 text-xs">{formatRelativeTime(s.swapped_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
