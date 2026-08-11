"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/formatters";

export default function DriverDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: driver, isLoading } = useQuery({
    queryKey: ["driver", id],
    queryFn: () => api.get(`/drivers/${id}`).then((r) => r.data),
    enabled: !!id,
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ["driver-sessions", id],
    queryFn: () => api.get(`/drivers/${id}/sessions`).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!driver) return <div className="p-6 text-slate-400">Driver not found.</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/drivers" className="hover:text-white">Drivers</Link>
        <span>/</span>
        <span className="text-white">{driver.full_name}</span>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{driver.full_name}</h1>
          <p className="text-slate-400 text-sm mt-1 font-telemetry">{driver.phone}</p>
        </div>
        <span className={`text-sm px-3 py-1 rounded-full ${
          driver.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"
        }`}>
          {driver.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {/* Assigned vehicle */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold mb-3">Assigned Vehicle</h3>
        {driver.assigned_vehicle_registration ? (
          <div className="flex items-center justify-between">
            <div>
              <div className="font-telemetry font-bold text-white">{driver.assigned_vehicle_registration}</div>
              <div className="text-xs text-slate-400">{driver.assigned_vehicle_model}</div>
            </div>
            <Link href={`/fleet/${driver.assigned_vehicle_id}`}
              className="text-blue-400 hover:text-blue-300 text-sm">
              View Vehicle →
            </Link>
          </div>
        ) : (
          <p className="text-slate-500 text-sm">No vehicle assigned</p>
        )}
      </div>

      {/* Recent sessions */}
      {sessions.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-4">Recent Sessions</h3>
          <div className="space-y-3">
            {sessions.slice(0, 10).map((s: any) => (
              <div key={s.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-telemetry text-white">{s.vehicle_registration}</span>
                  <span className="text-slate-400 ml-2">{s.energy_delivered_kwh?.toFixed(2)} kWh</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 text-xs">{formatRelativeTime(s.started_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
