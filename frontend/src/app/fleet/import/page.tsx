"use client";

import { useState } from "react";
import Link from "next/link";
import { fleetApi } from "@/lib/api";

export default function FleetImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ imported: number; errors: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await fleetApi.importCsv(formData);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Import failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
        <Link href="/fleet" className="hover:text-white">Fleet</Link>
        <span>/</span>
        <span className="text-white">Import CSV</span>
      </div>

      <h1 className="text-xl font-semibold mb-2">Bulk Import Vehicles</h1>
      <p className="text-slate-400 text-sm mb-6">
        Upload a CSV file to register multiple vehicles at once.
      </p>

      {/* CSV format guide */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 mb-6">
        <h3 className="text-sm font-semibold mb-3">Expected CSV Format</h3>
        <div className="font-telemetry text-xs text-slate-400 bg-slate-950 rounded-lg p-3 overflow-x-auto">
          <div className="text-slate-300">registration_number,model,vin,year,battery_chemistry,battery_capacity_kwh,max_range_km,oem_slug,city</div>
          <div>MH02AB1234,Ola S1 Pro,OLA1234567890,2023,LFP,3.97,181,ola_s1_pro,Mumbai</div>
          <div>KA01AB5678,Ather 450X,ATH9876543210,2023,NMC,2.9,146,ather_450x,Bengaluru</div>
        </div>
      </div>

      <form onSubmit={handleImport} className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm text-slate-400 mb-1.5">CSV File</label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
            className="block text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-500 file:text-white file:text-sm file:font-medium hover:file:bg-blue-600 file:cursor-pointer cursor-pointer"
          />
        </div>

        <button type="submit" disabled={loading || !file}
          className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors">
          {loading ? "Importing..." : "Import Vehicles"}
        </button>
      </form>

      {result && (
        <div className="mt-6 bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold mb-3">Import Results</h3>
          <p className="text-emerald-400 text-sm mb-2">
            Successfully imported {result.imported} vehicles
          </p>
          {result.errors.length > 0 && (
            <div>
              <p className="text-amber-400 text-sm mb-2">
                {result.errors.length} row(s) had errors:
              </p>
              <ul className="font-telemetry text-xs text-red-400 space-y-1">
                {result.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
