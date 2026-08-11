"use client";

import { useState } from "react";
import Link from "next/link";

export default function DispatchConfigPage() {
  const [config, setConfig] = useState({
    soc_threshold: 25,
    safety_buffer_km: 10,
    max_station_radius_km: 15,
  });
  const [saved, setSaved] = useState(false);

  const update = (field: string, value: number) =>
    setConfig((c) => ({ ...c, [field]: value }));

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // In production: PATCH /api/v1/dispatch/config
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-6 max-w-lg">
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
        <Link href="/dispatch" className="hover:text-white">Dispatch</Link>
        <span>/</span>
        <span className="text-white">Configure Thresholds</span>
      </div>

      <h1 className="text-xl font-semibold mb-2">Dispatch Configuration</h1>
      <p className="text-slate-400 text-sm mb-6">
        Tune when ChargeMesh issues charging recommendations for your fleet.
      </p>

      <form onSubmit={handleSave} className="bg-slate-900 rounded-xl border border-slate-800 p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            SoC Dispatch Threshold (%)
          </label>
          <p className="text-xs text-slate-500 mb-2">
            Issue recommendation when SoC drops below this value
          </p>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min={10}
              max={40}
              value={config.soc_threshold}
              onChange={(e) => update("soc_threshold", Number(e.target.value))}
              className="flex-1 accent-blue-500"
            />
            <span className="font-telemetry text-amber-400 text-xl font-bold w-16 text-right">
              {config.soc_threshold}%
            </span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Safety Buffer (km)
          </label>
          <p className="text-xs text-slate-500 mb-2">
            Require this extra range beyond the remaining route distance
          </p>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min={5}
              max={30}
              value={config.safety_buffer_km}
              onChange={(e) => update("safety_buffer_km", Number(e.target.value))}
              className="flex-1 accent-blue-500"
            />
            <span className="font-telemetry text-white text-xl font-bold w-16 text-right">
              {config.safety_buffer_km} km
            </span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Max Station Search Radius (km)
          </label>
          <p className="text-xs text-slate-500 mb-2">
            Only consider stations within this radius of the vehicle
          </p>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min={5}
              max={50}
              value={config.max_station_radius_km}
              onChange={(e) => update("max_station_radius_km", Number(e.target.value))}
              className="flex-1 accent-blue-500"
            />
            <span className="font-telemetry text-white text-xl font-bold w-16 text-right">
              {config.max_station_radius_km} km
            </span>
          </div>
        </div>

        <div className="pt-2">
          <button type="submit"
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors">
            {saved ? "Saved!" : "Save Configuration"}
          </button>
        </div>
      </form>

      <div className="mt-4 bg-slate-900/50 rounded-xl border border-slate-800 p-4 text-xs text-slate-400">
        <div className="font-semibold text-slate-300 mb-1">Dispatch Logic</div>
        Trigger condition: <span className="font-telemetry text-amber-400">SoC &lt; {config.soc_threshold}%</span>{" "}
        AND <span className="font-telemetry text-amber-400">estimated_range &lt; remaining_route + {config.safety_buffer_km} km</span>
      </div>
    </div>
  );
}
