/**
 * ChargeMesh — Number and Unit Formatters
 * Indian number formatting for currency, kWh, km values.
 */

export function formatINR(amount: number): string {
  if (amount >= 1_00_00_000) return `₹${(amount / 1_00_00_000).toFixed(2)}Cr`;
  if (amount >= 1_00_000) return `₹${(amount / 1_00_000).toFixed(2)}L`;
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(amount);
}

export function formatKWh(kwh: number): string {
  if (kwh >= 1000) return `${(kwh / 1000).toFixed(2)} MWh`;
  return `${kwh.toFixed(2)} kWh`;
}

export function formatKm(km: number): string {
  if (km >= 1000) return `${(km / 1000).toFixed(1)}k km`;
  return `${km.toFixed(1)} km`;
}

export function formatSoC(soc: number | null | undefined): string {
  if (soc == null) return "—";
  return `${soc.toFixed(1)}%`;
}

export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return "Never";
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.floor(diffHr / 24)}d ago`;
}

/** Returns CSS color class based on SoC level */
export function socColor(soc: number | null | undefined): string {
  if (soc == null) return "text-slate-400";
  if (soc > 40) return "text-emerald-400";
  if (soc > 20) return "text-amber-400";
  return "text-red-400";
}

/** Returns Tailwind bg color for battery SoC markers */
export function socBgColor(soc: number | null | undefined): string {
  if (soc == null) return "bg-slate-500";
  if (soc > 40) return "bg-emerald-500";
  if (soc > 20) return "bg-amber-500";
  return "bg-red-500";
}
