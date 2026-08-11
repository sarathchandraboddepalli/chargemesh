"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

interface Vehicle {
  id: string;
  registration_number: string;
  current_soc: number | null;
  current_latitude: number | null;
  current_longitude: number | null;
  status: string;
  driver_name?: string;
  estimated_range_km?: number;
}

interface Props {
  vehicles: Vehicle[];
}

export default function FleetLiveMap({ vehicles }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);

  // Default center: Mumbai (most vehicles)
  const [center] = useState<[number, number]>([72.8777, 19.0760]);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center,
      zoom: 11,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
  }, []);

  useEffect(() => {
    if (!map.current) return;

    // Clear existing markers
    markers.current.forEach((m) => m.remove());
    markers.current = [];

    // Add vehicle markers
    vehicles
      .filter((v) => v.current_latitude && v.current_longitude)
      .forEach((vehicle) => {
        const soc = vehicle.current_soc;

        // Colored dot based on SoC
        const color =
          soc == null ? "#64748b"
          : soc > 40 ? "#10B981"
          : soc > 20 ? "#F59E0B"
          : "#EF4444";

        const el = document.createElement("div");
        el.className = "vehicle-marker";
        el.style.cssText = `
          width: 14px;
          height: 14px;
          background: ${color};
          border: 2px solid rgba(255,255,255,0.6);
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 0 8px ${color}88;
        `;

        // Pulse animation for at-risk vehicles
        if (soc !== null && soc < 20) {
          el.style.animation = "pulse-glow 2s ease-in-out infinite";
        }

        const popup = new mapboxgl.Popup({ offset: 12, className: "chargemesh-popup" }).setHTML(`
          <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px;font-family:Inter,sans-serif;min-width:180px">
            <div style="font-family:'JetBrains Mono',monospace;font-weight:600;color:white;margin-bottom:8px">
              ${vehicle.registration_number}
            </div>
            <div style="color:${color};font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;margin-bottom:4px">
              ${soc != null ? soc.toFixed(1) + "%" : "—"}
            </div>
            <div style="color:#94a3b8;font-size:12px">State of Charge</div>
            ${vehicle.estimated_range_km ? `<div style="color:#94a3b8;font-size:12px;margin-top:4px">Range: ${vehicle.estimated_range_km.toFixed(0)} km</div>` : ""}
            ${vehicle.driver_name ? `<div style="color:#94a3b8;font-size:12px;margin-top:4px">Driver: ${vehicle.driver_name}</div>` : ""}
            <div style="color:#64748b;font-size:11px;margin-top:6px;text-transform:capitalize">${vehicle.status}</div>
          </div>
        `);

        const marker = new mapboxgl.Marker(el)
          .setLngLat([vehicle.current_longitude!, vehicle.current_latitude!])
          .setPopup(popup)
          .addTo(map.current!);

        markers.current.push(marker);
      });
  }, [vehicles]);

  return (
    <div ref={mapContainer} style={{ width: "100%", height: "100%" }} />
  );
}
