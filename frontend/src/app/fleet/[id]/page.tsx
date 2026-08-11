"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { fleetApi, batteryApi } from "@/lib/api";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { formatRelativeTime } from "@/lib/formatters";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function socColor(soc: number | null) {
  if (soc == null) return "text-slate-400";
  if (soc > 40) return "text-emerald-400";
  if (soc > 20) return "text-amber-400";
  return "text-red-400";
}

export default function VehicleDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: vehicle, isLoading } = useQuery({
    queryKey: ["fleet-vehicle", id],
    queryFn: () => fleetApi.getVehicle(id).then((r) => r.data),
    enabled: !!id,
  });

  const { data: battery } = useQuery({
    queryKey: ["vehicle-battery", id],
    queryFn: () => batteryApi.getByVehicle(id).then((r) => r.data),
    enabled: !!id,
  });

  const { records, connected } = useTelemetryStream(id);

  if (isLoading) {
    return <div className="p-6 text-slate-400">Loading vehicle data...</div>;
  }

  if (!vehicle) {
    return <div className="p-6 text-slate-400">Vehicle not found.</div>;
  }

  const socData = records.slice(-50).map((r) => ({
    time: new Date(r.recorded_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    soc: r.state_of_charge_pct,
    temp: r.battery_temp_celsius,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/fleet" className="hover:text-white">Fleet</Link>
        <span>/</span>
        <span className="font-telemetry font-semibold text-white">{vehicle.registration_number}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold font-telemetry">{vehicle.registration_number}</h1>
          <p className="text-slate-400 text-sm mt-1">{vehicle.model} — {vehicle.oem_slug}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-slate-600"}`} />
          <span className="text-xs text-slate-400">{connected ? "Live stream" : "Polling"}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          {
            label: "State of Charge",
            value: vehicle.current_soc != null ? `${vehicle.current_soc.toFixed(1)}%` : "—",
            color: socColor(vehicle.current_soc),
          },
          {
            label: "Est. Range",
            value: vehicle.estimated_range_km != null ? `${vehicle.estimated_range_km.toFixed(0)} km` : "—",
            color: "text-white",
          },
          {
            label: "Battery SoH",
            value: battery?.current_soh != null ? `${battery.current_soh.toFixed(1)}%` : "—",
            color: battery?.current_soh > 80 ? "text-emerald-400" : "text-amber-400",
          },
          {
            label: "Thermal Stress",
            value: battery?.accumulated_thermal_stress != null
              ? `${battery.accumulated_thermal_stress.toFixed(1)} °C·h`
              : "—",
            color: battery?.is_flagged ? "text-red-400" : "text-white",
          },
        ].map((s) => (
          <div key={s.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <div className={`font-telemetry text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Live telemetry charts */}
      {records.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">SoC Over Time</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={socData}>
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#64748b" }} unit="%" />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                  itemStyle={{ color: "#10B981", fontSize: 12 }}
                />
                <Line type="monotone" dataKey="soc" stroke="#10B981" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
            <h3 className="text-sm font-semibold mb-3 text-slate-300">Battery Temp (°C)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={socData}>
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis domain={[20, 55]} tick={{ fontSize: 10, fill: "#64748b" }} unit="°C" />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  labelStyle={{ color: "#94a3b8", fontSize: 11 }}
                  itemStyle={{ color: "#F59E0B", fontSize: 12 }}
                />
                <Line type="monotone" dataKey="temp" stroke="#F59E0B" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Vehicle info */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold mb-4">Vehicle Details</h3>
        <dl className="grid grid-cols-3 gap-4 text-sm">
          {[
            ["VIN", vehicle.vin ?? "—"],
            ["Year", vehicle.year ?? "—"],
            ["Battery Chemistry", vehicle.battery_chemistry ?? "—"],
            ["Battery Capacity", vehicle.battery_capacity_kwh ? `${vehicle.battery_capacity_kwh} kWh` : "—"],
            ["Max Range", vehicle.max_range_km ? `${vehicle.max_range_km} km` : "—"],
            ["City", vehicle.city ?? "—"],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-slate-400">{label}</dt>
              <dd className="text-white font-telemetry mt-0.5">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Battery health */}
      {battery && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Battery Health</h3>
            {battery.is_flagged && (
              <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
                Flagged for inspection
              </span>
            )}
          </div>
          <dl className="grid grid-cols-4 gap-4 text-sm">
            {[
              ["Serial", battery.serial_number],
              ["Cycle Count", battery.cycle_count?.toLocaleString()],
              ["SoH", `${battery.current_soh?.toFixed(2)}%`],
              ["Thermal Stress", `${battery.accumulated_thermal_stress?.toFixed(1)} °C·h`],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-slate-400">{label}</dt>
                <dd className="text-white font-telemetry mt-0.5">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
