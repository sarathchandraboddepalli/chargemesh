/**
 * ChargeMesh API Client
 * Base Axios instance with JWT auth and error handling.
 */

import axios from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const refreshToken = Cookies.get("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          Cookies.set("access_token", data.access_token, { expires: 1 / 96 }); // 15 min
          Cookies.set("refresh_token", data.refresh_token, { expires: 30 });
          err.config.headers.Authorization = `Bearer ${data.access_token}`;
          return axios(err.config);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/auth/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

// Fleet API
export const fleetApi = {
  getSummary: () => api.get("/fleet/summary"),
  getVehicles: (params?: Record<string, string>) =>
    api.get("/fleet/vehicles", { params }),
  getVehicle: (id: string) => api.get(`/fleet/vehicles/${id}`),
  getTelemetry: (id: string, hours = 24) =>
    api.get(`/fleet/vehicles/${id}/telemetry`, { params: { hours } }),
  importCsv: (formData: FormData) =>
    api.post("/fleet/vehicles/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

// Dispatch API
export const dispatchApi = {
  getRecommendations: (params?: Record<string, string>) =>
    api.get("/dispatch/recommendations", { params }),
  getVehicleRecommendation: (vehicleId: string) =>
    api.get(`/dispatch/vehicle/${vehicleId}`),
  acknowledge: (id: string) =>
    api.post(`/dispatch/recommendations/${id}/acknowledge`),
  getConfig: () => api.get("/dispatch/config"),
};

// Stations API
export const stationsApi = {
  getAll: (params?: Record<string, string>) =>
    api.get("/stations", { params }),
  get: (id: string) => api.get(`/stations/${id}`),
  getNearby: (lat: number, lng: number, radiusKm = 10) =>
    api.get("/stations/nearby", {
      params: { latitude: lat, longitude: lng, radius_km: radiusKm },
    }),
};

// Sessions API
export const sessionsApi = {
  getAll: (status?: string, params?: Record<string, string>) =>
    api.get("/sessions", { params: { ...(status ? { status } : {}), ...params } }),
  get: (id: string) => api.get(`/sessions/${id}`),
  getByStation: (stationId: string) =>
    api.get("/sessions", { params: { station_id: stationId } }),
  getActive: () => api.get("/sessions/active"),
  book: (vehicleId: string, stationId: string) =>
    api.post("/sessions/book", { vehicle_id: vehicleId, station_id: stationId }),
  start: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/start`),
  stop: (sessionId: string) =>
    api.post(`/sessions/${sessionId}/stop`),
};

// Battery API
export const batteryApi = {
  getAll: (flaggedOnly?: boolean) =>
    api.get("/batteries", { params: flaggedOnly ? { flagged: true } : {} }),
  get: (id: string) => api.get(`/batteries/${id}`),
  getByVehicle: (vehicleId: string) =>
    api.get(`/batteries/by-vehicle/${vehicleId}`),
  getThermalHistory: (batteryId: string) =>
    api.get(`/batteries/${batteryId}/thermal-history`),
  getSwaps: (batteryId: string) =>
    api.get(`/batteries/${batteryId}/swaps`),
};

// Thermal API
export const thermalApi = {
  getAlerts: (severity?: string) =>
    api.get("/thermal/alerts", { params: severity ? { severity } : {} }),
  getActiveAlerts: () => api.get("/thermal/alerts", { params: { active: true } }),
  getByBattery: (batteryId: string) =>
    api.get(`/thermal/batteries/${batteryId}/alerts`),
  getFleetSummary: () => api.get("/thermal/fleet-summary"),
};

// Ledger API
export const ledgerApi = {
  getReports: () => api.get("/ledger/reports"),
  getReport: (id: string) => api.get(`/ledger/reports/${id}`),
  approveReport: (id: string) => api.post(`/ledger/reports/${id}/approve`),
  getSettlements: () => api.get("/ledger/settlements"),
  getPricingConfigs: () => api.get("/ledger/pricing"),
  createPricingConfig: (data: Record<string, unknown>) =>
    api.post("/ledger/pricing", data),
};

// Analytics API
export const analyticsApi = {
  getOverview: () => api.get("/analytics/overview"),
  getSoCDistribution: () => api.get("/analytics/soc-distribution"),
  getDispatchAccuracy: () => api.get("/analytics/dispatch-accuracy"),
  getDegradationTrend: () => api.get("/analytics/degradation-trend"),
};
