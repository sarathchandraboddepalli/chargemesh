import { useEffect, useState, useRef } from "react";
import Cookies from "js-cookie";

interface TelemetryRecord {
  vehicle_id: string;
  recorded_at: string;
  state_of_charge_pct: number;
  battery_temp_celsius: number;
  latitude: number | null;
  longitude: number | null;
  speed_kmph: number;
  odometer_km: number;
  estimated_range_km: number;
}

export function useTelemetryStream(vehicleId: string | null) {
  const [records, setRecords] = useState<TelemetryRecord[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!vehicleId) return;

    const token = Cookies.get("access_token");
    const url = `${process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000"}/api/v1/telemetry/stream/${vehicleId}?token=${token}`;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => setConnected(true);
    ws.current.onclose = () => setConnected(false);
    ws.current.onerror = () => setConnected(false);

    ws.current.onmessage = (event) => {
      try {
        const record: TelemetryRecord = JSON.parse(event.data);
        setRecords((prev) => {
          const next = [...prev, record];
          // Keep last 100 records
          return next.slice(-100);
        });
      } catch {
        // Ignore parse errors
      }
    };

    return () => {
      ws.current?.close();
    };
  }, [vehicleId]);

  return { records, connected };
}
