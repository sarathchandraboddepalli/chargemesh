"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { thermalApi, batteryApi } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from "recharts";
import { formatRelativeTime } from "@/lib/formatters";

export default function BatteryThermalPage() {
  const { battery_id } = useParams<{ battery_id: string }>();

  const { data: battery } = useQuery({
    queryKey: ["battery", battery_id],
    queryFn: () => batteryApi.get(battery_id).then((r) => r.data),
    enabled: !!battery_id,
  });

  const { data: alerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ["thermal-alerts-battery", battery_id],
    queryFn: () => thermalApi.getByBattery(battery_id).then((r) => r.data),
    enabled: !!battery_id,
  });

  const { data: thermalHistory = [] } = useQuery({
    queryKey: ["battery-thermal", battery_id],
    queryFn: () => batteryApi.getThermalHistory(battery_id).then((r) => r.data),
    enabled: !!battery_id,
  });

  const chartData = thermalHistory.slice(-200).map((r: any) => ({
    time: new Date(r.recorded_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    temp: r.battery_temp_celsius,
  }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/thermal" className="hover:text-white">Thermal</Link>
        <span>/</span>
        <span className="text-white font-telemetry">{battery?.serial_number ?? battery_id?.slice(0, 8)}</span>
      </div>

      <div>
        <h1 className="text-xl font-semibold">
          Thermal History — <span className="font-telemetry">{battery?.serial_number ?? "Battery"}</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Accumulated stress: <span className="text-amber-400 font-telemetry font-semibold">
            {battery?.accumulated_thermal_stress?.toFixed(1) ?? "—"} °C·h
          </span>
          {" "}(degree-hours above 35°C baseline)
        </p>
      </div>

      {/* Temperature chart */}
      {chartData.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Temperature Over Time</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis domain={[20, 60]} tick={{ fontSize: 10, fill: "#64748b" }} unit="°C" />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                itemStyle={{ color: "#F59E0B", fontSize: 12 }}
              />
              <ReferenceLine y={35} stroke="#64748b" strokeDasharray="4 4"
                label={{ value: "Baseline 35°C", fill: "#64748b", fontSize: 9, position: "right" }} />
              <ReferenceLine y={42} stroke="#F59E0B" strokeDasharray="4 4"
                label={{ value: "Warning 42°C", fill: "#F59E0B", fontSize: 9, position: "right" }} />
              <ReferenceLine y={48} stroke="#EF4444" strokeDasharray="4 4"
                label={{ value: "Critical 48°C", fill: "#EF4444", fontSize: 9, position: "right" }} />
              <Line type="monotone" dataKey="temp" stroke="#F59E0B" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Alert history */}
      <div>
        <h3 className="text-sm font-semibold mb-3">Alert History ({alerts.length})</h3>
        {alertsLoading && <div className="text-slate-500 text-sm">Loading...</div>}
        {!alertsLoading && alerts.length === 0 && (
          <div className="text-slate-500 text-sm">No thermal alerts for this battery</div>
        )}
        <div className="space-y-2">
          {alerts.map((alert: any) => (
            <div key={alert.id} className={`p-3 rounded-lg border text-sm flex items-center justify-between ${
              alert.severity === "critical"
                ? "bg-red-500/10 border-red-500/20 text-red-300"
                : "bg-amber-500/10 border-amber-500/20 text-amber-300"
            }`}>
              <div>
                <span className="font-semibold capitalize">{alert.severity}</span>
                {" — "}
                <span>{alert.alert_type.replace(/_/g, " ")}</span>
                <span className="font-telemetry font-bold ml-2">{alert.temperature_celsius?.toFixed(1)}°C</span>
              </div>
              <span className="text-xs opacity-60">{formatRelativeTime(alert.created_at)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
