import { useQuery } from "@tanstack/react-query";
import { fleetApi } from "@/lib/api";

export function useFleetSummary() {
  return useQuery({
    queryKey: ["fleet-summary"],
    queryFn: () => fleetApi.getSummary().then((r) => r.data),
  });
}

export function useVehicles() {
  return useQuery({
    queryKey: ["fleet-vehicles"],
    queryFn: () => fleetApi.getVehicles().then((r) => r.data),
  });
}

export function useVehicle(id: string) {
  return useQuery({
    queryKey: ["fleet-vehicle", id],
    queryFn: () => fleetApi.getVehicle(id).then((r) => r.data),
    enabled: !!id,
  });
}
