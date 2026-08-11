/**
 * ChargeMesh Driver App — API Service
 *
 * SECURITY: Location data from the device is used LOCALLY for distance calculation
 * when finding nearby stations. It is NEVER sent to the backend API.
 * Vehicle location comes exclusively from OEM telemetry on the server side.
 */

import axios from "axios";
import * as SecureStore from "expo-secure-store";
import Constants from "expo-constants";

const API_URL = Constants.expoConfig?.extra?.apiUrl ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Attach token on every request
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync("access_token");
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
      const refreshToken = await SecureStore.getItemAsync("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          await SecureStore.setItemAsync("access_token", data.access_token);
          await SecureStore.setItemAsync("refresh_token", data.refresh_token);
          err.config.headers.Authorization = `Bearer ${data.access_token}`;
          return axios(err.config);
        } catch {
          await SecureStore.deleteItemAsync("access_token");
          await SecureStore.deleteItemAsync("refresh_token");
          // Navigation handled by app root
        }
      }
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (email: string, phone: string, password: string) =>
    api.post("/auth/register", { email, phone, password }),
  me: () => api.get("/auth/me"),
};

export const driverApi = {
  // Get assigned vehicle state (SoC comes from OEM telemetry, not device GPS)
  getVehicleState: () => api.get("/driver/vehicle"),

  // Get dispatch recommendation for current vehicle
  getRecommendation: () => api.get("/driver/recommendation"),

  // Get nearby stations — lat/lng computed on device for proximity,
  // but NOT stored server-side (driver location privacy requirement)
  getNearbyStations: (lat: number, lng: number, radiusKm = 10) =>
    api.get("/driver/stations/nearby", {
      params: { latitude: lat, longitude: lng, radius_km: radiusKm },
    }),

  // Get active charging session
  getActiveSession: () => api.get("/driver/session/active"),

  // Start session at a station
  startSession: (stationId: string, connectorId: number) =>
    api.post("/driver/session/start", { station_id: stationId, connector_id: connectorId }),

  // Stop session
  stopSession: () => api.post("/driver/session/stop"),

  // Get session history
  getHistory: (limit = 20) =>
    api.get("/driver/sessions/history", { params: { limit } }),

  // Report a battery swap
  reportSwap: (batteryId: string, kwhConsumed: number) =>
    api.post("/driver/swap/report", { battery_id: batteryId, kwh_consumed: kwhConsumed }),

  // Update FCM token for push notifications
  updatePushToken: (token: string) =>
    api.post("/driver/push-token", { token }),
};
