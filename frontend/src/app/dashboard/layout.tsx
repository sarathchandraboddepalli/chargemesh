"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { logout } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "⊞" },
  { href: "/fleet", label: "Fleet", icon: "🚗" },
  { href: "/stations", label: "Stations", icon: "⚡" },
  { href: "/sessions", label: "Sessions", icon: "🔌" },
  { href: "/batteries", label: "Batteries", icon: "🔋" },
  { href: "/dispatch", label: "Dispatch", icon: "📍" },
  { href: "/ledger", label: "Ledger", icon: "📊" },
  { href: "/thermal", label: "Thermal", icon: "🌡" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-500 rounded flex items-center justify-center text-xs font-bold">
              CM
            </div>
            <span className="font-semibold text-sm">ChargeMesh</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  active
                    ? "bg-blue-500/20 text-blue-400 font-medium"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                )}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Settings + Logout */}
        <div className="p-3 border-t border-slate-800 space-y-0.5">
          <Link
            href="/settings/networks"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <span>⚙</span> Settings
          </Link>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
          >
            <span>→</span> Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
