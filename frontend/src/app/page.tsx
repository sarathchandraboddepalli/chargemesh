import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center font-bold text-white text-sm">
            CM
          </div>
          <span className="font-semibold text-lg">ChargeMesh</span>
        </div>
        <div className="flex gap-4">
          <Link href="/auth/login" className="text-slate-400 hover:text-white transition-colors">
            Login
          </Link>
          <Link
            href="/auth/register"
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-6xl mx-auto px-8 py-24">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 text-blue-400 text-sm mb-8">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            EV Infrastructure Operating System
          </div>
          <h1 className="text-5xl font-bold mb-6 leading-tight">
            One dashboard for every<br />
            <span className="text-blue-400">EV on your fleet</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            ChargeMesh aggregates fragmented EV infrastructure — 4 charging networks, 2 battery swap vendors,
            3 OEMs — into a single operational layer for India's commercial EV market.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/auth/register"
              className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Start Free Trial
            </Link>
            <Link
              href="/dashboard"
              className="border border-slate-700 hover:border-slate-500 text-slate-300 px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              View Demo Dashboard
            </Link>
          </div>
        </div>

        {/* ROI Calculator */}
        <div className="grid grid-cols-3 gap-6 mb-24">
          {[
            { label: "Fleet Size", value: "3,000 EVs", icon: "🚗" },
            { label: "Charging Downtime Reduction", value: "30%", icon: "⚡" },
            { label: "Annual Savings", value: "₹75L+", icon: "💰" },
          ].map((stat) => (
            <div key={stat.label} className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center">
              <div className="text-3xl mb-3">{stat.icon}</div>
              <div className="font-telemetry text-2xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-slate-400 text-sm">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="grid grid-cols-2 gap-8">
          {[
            {
              title: "Predictive Dispatch",
              description: "Know which vehicles need charging 45 minutes before they run out. Pre-book slots automatically.",
              badge: "Core",
            },
            {
              title: "BaaS Unified Ledger",
              description: "Automated settlement calculations between fleet operators and battery swap vendors. No more spreadsheets.",
              badge: "Premium",
            },
            {
              title: "Thermal Intelligence",
              description: "India-specific battery health monitoring. Alerts before failures — not after. Thermal stress scoring per battery.",
              badge: "Premium",
            },
            {
              title: "OCPP Charging Aggregation",
              description: "One API to book slots on ChargeZone, Statiq, Tata Power EV. Real-time station availability.",
              badge: "Core",
            },
          ].map((feature) => (
            <div key={feature.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <h3 className="font-semibold text-white">{feature.title}</h3>
                <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">
                  {feature.badge}
                </span>
              </div>
              <p className="text-slate-400 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
