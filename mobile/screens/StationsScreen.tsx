/**
 * StationsScreen
 *
 * PRIVACY: Uses device GPS to find nearby stations for distance calculation.
 * The coordinates are passed as query parameters to the API but are NOT stored
 * server-side — the backend uses them only to compute distances and returns
 * sorted results.
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Linking,
  Alert,
} from "react-native";
import * as Location from "expo-location";
import { StationCard } from "../components/StationCard";
import { driverApi } from "../services/api";

interface Station {
  id: string;
  name: string;
  address: string;
  distance_km?: number;
  available_connectors: number;
  total_connectors: number;
  price_per_kwh_inr: number;
  connector_types: string[];
  network_name: string;
  is_operational: boolean;
  latitude?: number;
  longitude?: number;
}

export function StationsScreen() {
  const [stations, setStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [locationGranted, setLocationGranted] = useState(false);

  useEffect(() => {
    loadNearbyStations();
  }, []);

  const loadNearbyStations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setError("Location access denied. Showing all stations.");
        // Fall back to city-level results without coords
        const { data } = await driverApi.getNearbyStations(19.076, 72.877, 25);
        setStations(data);
        return;
      }

      setLocationGranted(true);
      const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const { latitude, longitude } = location.coords;

      // NOTE: These coordinates are used for proximity sorting only.
      // The API does NOT store them. See services/api.ts for the privacy note.
      const { data } = await driverApi.getNearbyStations(latitude, longitude, 15);
      setStations(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to load stations");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNavigate = (station: Station) => {
    if (station.latitude && station.longitude) {
      const url = `https://maps.google.com/?q=${station.latitude},${station.longitude}`;
      Linking.openURL(url);
    } else {
      Alert.alert("Navigation", `Search for "${station.name}" in Google Maps.`);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Nearby Stations</Text>
        <Text style={styles.subtitle}>
          {locationGranted ? "Within 15 km of your location" : "Showing city stations"}
        </Text>
      </View>

      {/* Privacy notice */}
      <View style={styles.privacyNote}>
        <Text style={styles.privacyText}>
          Your location is used only to sort stations by distance and is not stored.
        </Text>
      </View>

      {isLoading && (
        <View style={styles.center}>
          <ActivityIndicator color="#3B82F6" size="large" />
          <Text style={styles.loadingText}>Finding nearby stations...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {!isLoading && stations.map((station) => (
        <StationCard
          key={station.id}
          station={station}
          onNavigate={() => handleNavigate(station)}
        />
      ))}

      {!isLoading && stations.length === 0 && !error && (
        <View style={styles.center}>
          <Text style={styles.emptyText}>No charging stations found nearby</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  content: {
    paddingBottom: 32,
    paddingHorizontal: 16,
  },
  header: {
    paddingTop: 60,
    paddingBottom: 12,
  },
  title: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
  },
  subtitle: {
    color: "#64748b",
    fontSize: 13,
    marginTop: 2,
  },
  privacyNote: {
    backgroundColor: "#1e293b",
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#334155",
  },
  privacyText: {
    color: "#64748b",
    fontSize: 11,
    textAlign: "center",
  },
  center: {
    alignItems: "center",
    paddingVertical: 40,
  },
  loadingText: {
    color: "#64748b",
    marginTop: 12,
    fontSize: 13,
  },
  errorBox: {
    backgroundColor: "#1a0000",
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#7f1d1d",
  },
  errorText: {
    color: "#f87171",
    fontSize: 13,
    textAlign: "center",
  },
  emptyText: {
    color: "#64748b",
    fontSize: 14,
  },
});
