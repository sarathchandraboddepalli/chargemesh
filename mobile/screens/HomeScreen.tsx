import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  TouchableOpacity,
  Linking,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { SoCGauge } from "../components/SoCGauge";
import { RecommendationCard } from "../components/RecommendationCard";
import { useVehicle } from "../hooks/useVehicle";
import { driverApi } from "../services/api";

interface Recommendation {
  id: string;
  trigger_soc: number;
  estimated_range_km: number;
  recommended_station: any;
  recommended_at: string;
  was_acted_upon: boolean;
}

export function HomeScreen() {
  const { vehicle, isLoading, error, lastUpdated, isFromCache, refresh } = useVehicle();
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadRecommendation = async () => {
    try {
      const { data } = await driverApi.getRecommendation();
      setRecommendation(data);
    } catch {
      // No recommendation or network error — keep previous
    }
  };

  useEffect(() => {
    loadRecommendation();
  }, [vehicle]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refresh();
    await loadRecommendation();
    setRefreshing(false);
  }, [refresh]);

  const handleNavigate = (station: any) => {
    if (station?.latitude && station?.longitude) {
      const url = `https://maps.google.com/?q=${station.latitude},${station.longitude}`;
      Linking.openURL(url);
    }
  };

  const tempColor =
    vehicle?.battery_temp_celsius == null ? "#64748b"
    : vehicle.battery_temp_celsius >= 48 ? "#EF4444"
    : vehicle.battery_temp_celsius >= 42 ? "#F59E0B"
    : "#10B981";

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#3B82F6"
          colors={["#3B82F6"]}
        />
      }
    >
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Good day</Text>
        {vehicle && (
          <Text style={styles.vehicleReg}>{vehicle.registration_number}</Text>
        )}
      </View>

      {/* Offline / stale banner */}
      {(isFromCache || vehicle?.is_stale) && (
        <View style={styles.staleBanner}>
          <Text style={styles.staleText}>
            {isFromCache ? "Offline mode" : "Telemetry stale"} — last updated{" "}
            {lastUpdated ? formatRelative(lastUpdated) : "unknown"}
          </Text>
        </View>
      )}

      {/* Error */}
      {error && !vehicle && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* SoC Gauge */}
      <View style={styles.gaugeContainer}>
        <SoCGauge soc={vehicle?.current_soc ?? null} size={200} />
        {vehicle?.estimated_range_km != null && (
          <View style={styles.rangeRow}>
            <Text style={styles.rangeValue}>
              {vehicle.estimated_range_km.toFixed(0)} km
            </Text>
            <Text style={styles.rangeLabel}> estimated range</Text>
          </View>
        )}
      </View>

      {/* Battery stats */}
      {vehicle && (
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={[styles.statValue, { color: tempColor }]}>
              {vehicle.battery_temp_celsius != null
                ? `${vehicle.battery_temp_celsius.toFixed(1)}°C`
                : "—"}
            </Text>
            <Text style={styles.statLabel}>Battery Temp</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statValue}>{vehicle.model}</Text>
            <Text style={styles.statLabel}>Vehicle</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statValue, { color: vehicle.status === "active" ? "#10B981" : "#64748b" }]}>
              {vehicle.status}
            </Text>
            <Text style={styles.statLabel}>Status</Text>
          </View>
        </View>
      )}

      {/* Dispatch recommendation */}
      <Text style={styles.sectionTitle}>Charging Status</Text>
      <RecommendationCard
        recommendation={recommendation}
        isFromCache={isFromCache}
        lastUpdated={lastUpdated}
        onNavigate={handleNavigate}
      />

      {/* Privacy notice */}
      <View style={styles.privacyNotice}>
        <Text style={styles.privacyText}>
          Your device location is used only to find nearby stations and is never sent to ChargeMesh servers.
          Vehicle position comes from manufacturer telemetry.
        </Text>
      </View>
    </ScrollView>
  );
}

function formatRelative(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  return `${Math.floor(diffMin / 60)}h ago`;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  content: {
    paddingBottom: 32,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 8,
  },
  greeting: {
    color: "#64748b",
    fontSize: 14,
  },
  vehicleReg: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
    marginTop: 2,
  },
  staleBanner: {
    backgroundColor: "#1c1917",
    borderWidth: 1,
    borderColor: "#78350f",
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  staleText: {
    color: "#fbbf24",
    fontSize: 12,
    textAlign: "center",
  },
  errorBanner: {
    backgroundColor: "#1a0000",
    borderWidth: 1,
    borderColor: "#7f1d1d",
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 8,
    padding: 12,
  },
  errorText: {
    color: "#f87171",
    fontSize: 13,
    textAlign: "center",
  },
  gaugeContainer: {
    alignItems: "center",
    paddingVertical: 24,
  },
  rangeRow: {
    flexDirection: "row",
    alignItems: "baseline",
    marginTop: 8,
  },
  rangeValue: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
  rangeLabel: {
    color: "#64748b",
    fontSize: 14,
  },
  statsRow: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginBottom: 20,
    backgroundColor: "#1e293b",
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: "#334155",
  },
  statBox: {
    flex: 1,
    alignItems: "center",
  },
  statValue: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
    fontVariant: ["tabular-nums"],
    marginBottom: 2,
  },
  statLabel: {
    color: "#64748b",
    fontSize: 11,
  },
  statDivider: {
    width: 1,
    backgroundColor: "#334155",
    marginVertical: 4,
  },
  sectionTitle: {
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginHorizontal: 20,
    marginBottom: 8,
  },
  privacyNotice: {
    marginHorizontal: 16,
    marginTop: 20,
    padding: 12,
    backgroundColor: "#0f172a",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#1e293b",
  },
  privacyText: {
    color: "#475569",
    fontSize: 11,
    lineHeight: 16,
    textAlign: "center",
  },
});
