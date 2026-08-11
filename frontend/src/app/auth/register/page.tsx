"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", phone: "", password: "", org_name: "", org_type: "fleet" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form.email, form.password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center font-bold text-white text-lg mx-auto mb-3">
            CM
          </div>
          <h1 className="text-xl font-semibold">Create your ChargeMesh account</h1>
          <p className="text-slate-400 text-sm mt-1">India's commercial EV infrastructure layer</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-slate-900 rounded-xl p-6 space-y-4 border border-slate-800">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm text-slate-400 mb-1.5">Work Email</label>
              <input type="email" value={form.email} onChange={update("email")} required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="[REDACTED_EMAIL_ADDRESS_2]" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm text-slate-400 mb-1.5">Phone Number</label>
              <input type="tel" value={form.phone} onChange={update("phone")} required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="+91 98765 43210" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm text-slate-400 mb-1.5">Password</label>
              <input type="password" value={form.password} onChange={update("password")} required minLength={8}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="Minimum 8 characters" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm text-slate-400 mb-1.5">Organisation Name</label>
              <input type="text" value={form.org_name} onChange={update("org_name")} required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                placeholder="Blue Dart Express Fleet" />
            </div>
            <div className="col-span-2">
              <label className="block text-sm text-slate-400 mb-1.5">Organisation Type</label>
              <select value={form.org_type} onChange={update("org_type")}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
                <option value="fleet">Fleet Operator</option>
                <option value="baas_vendor">BaaS Vendor</option>
                <option value="charging_network">Charging Network</option>
              </select>
            </div>
          </div>

          <button type="submit" disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-semibold transition-colors">
            {loading ? "Creating account..." : "Create account"}
          </button>

          <p className="text-center text-slate-500 text-sm">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
