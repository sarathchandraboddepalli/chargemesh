import { useState, useEffect, useCallback } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { driverApi } from "../services/api";

const CACHE_KEY = "chargemesh:vehicle_state";
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

interface VehicleState {
  id: string;
  registration_number: string;
  model: string;
  current_soc: number | null;
  estimated_range_km: number | null;
  battery_temp_celsius: number | null;
  status: string;
  last_telemetry_at: string | null;
  is_stale: boolean;
}

interface CachedState {
  data: VehicleState;
  cachedAt: number;
}

export function useVehicle() {
  const [vehicle, setVehicle] = useState<VehicleState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isFromCache, setIsFromCache] = useState(false);

  const loadFromCache = async (): Promise<VehicleState | null> => {
    try {
      const raw = await AsyncStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      const cached: CachedState = JSON.parse(raw);
      const age = Date.now() - cached.cachedAt;
      if (age < CACHE_TTL_MS) {
        return cached.data;
      }
      return null;
    } catch {
      return null;
    }
  };

  const saveToCache = async (data: VehicleState) => {
    try {
      const cached: CachedState = { data, cachedAt: Date.now() };
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(cached));
    } catch {
      // Ignore cache write errors
    }
  };

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await driverApi.getVehicleState();
      setVehicle(data);
      setLastUpdated(new Date());
      setIsFromCache(false);
      await saveToCache(data);
    } catch (err: any) {
      // Try cache fallback on network error
      const cached = await loadFromCache();
      if (cached) {
        setVehicle(cached);
        setIsFromCache(true);
        setError("Offline — showing cached data");
      } else {
        setError(err?.response?.data?.detail ?? "Failed to load vehicle data");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Load from cache immediately, then refresh from API
    loadFromCache().then((cached) => {
      if (cached) {
        setVehicle(cached);
        setIsFromCache(true);
        setIsLoading(false);
      }
    });
    refresh();

    // Refresh every 2 minutes
    const interval = setInterval(refresh, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [refresh]);

  return {
    vehicle,
    isLoading,
    error,
    lastUpdated,
    isFromCache,
    refresh,
  };
}
