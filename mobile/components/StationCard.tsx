import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

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
}

interface Props {
  station: Station;
  onPress?: () => void;
  onNavigate?: () => void;
}

export function StationCard({ station, onPress, onNavigate }: Props) {
  const avail = station.available_connectors;
  const total = station.total_connectors;
  const pct = total ? (avail / total) * 100 : 0;

  const availColor =
    avail === 0 ? "#EF4444"
    : avail < total / 2 ? "#F59E0B"
    : "#10B981";

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.name}>{station.name}</Text>
          <View style={[styles.statusDot, { backgroundColor: station.is_operational ? "#10B981" : "#EF4444" }]} />
        </View>
        <Text style={styles.network}>{station.network_name}</Text>
      </View>

      {station.distance_km != null && (
        <Text style={styles.distance}>{station.distance_km.toFixed(1)} km away</Text>
      )}

      {/* Availability bar */}
      <View style={styles.availRow}>
        <View style={styles.barContainer}>
          <View style={[styles.barFill, { width: `${pct}%`, backgroundColor: availColor }]} />
        </View>
        <Text style={[styles.availText, { color: availColor }]}>
          {avail}/{total}
        </Text>
      </View>

      <View style={styles.footer}>
        <Text style={styles.price}>₹{station.price_per_kwh_inr}/kWh</Text>
        <View style={styles.connectors}>
          {station.connector_types.slice(0, 3).map((ct) => (
            <View key={ct} style={styles.connectorChip}>
              <Text style={styles.connectorText}>{ct}</Text>
            </View>
          ))}
        </View>
      </View>

      {onNavigate && station.is_operational && avail > 0 && (
        <TouchableOpacity style={styles.navBtn} onPress={onNavigate}>
          <Text style={styles.navBtnText}>Navigate →</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#1e293b",
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  header: {
    marginBottom: 6,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  name: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
    flex: 1,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  network: {
    color: "#64748b",
    fontSize: 12,
    marginTop: 2,
  },
  distance: {
    color: "#3B82F6",
    fontSize: 12,
    marginBottom: 8,
  },
  availRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  barContainer: {
    flex: 1,
    height: 4,
    backgroundColor: "#1e293b",
    borderRadius: 2,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#334155",
  },
  barFill: {
    height: "100%",
    borderRadius: 2,
  },
  availText: {
    fontSize: 11,
    fontVariant: ["tabular-nums"],
    width: 30,
    textAlign: "right",
  },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  price: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
    fontVariant: ["tabular-nums"],
  },
  connectors: {
    flexDirection: "row",
    gap: 4,
  },
  connectorChip: {
    backgroundColor: "#0f172a",
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: "#334155",
  },
  connectorText: {
    color: "#94a3b8",
    fontSize: 10,
  },
  navBtn: {
    backgroundColor: "#3B82F6",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
    marginTop: 12,
  },
  navBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 13,
  },
});
