import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

interface Station {
  id: string;
  name: string;
  distance_km: number;
  available_connectors: number;
  price_per_kwh_inr: number;
}

interface Recommendation {
  id: string;
  trigger_soc: number;
  estimated_range_km: number;
  recommended_station: Station | null;
  recommended_at: string;
  was_acted_upon: boolean;
}

interface Props {
  recommendation: Recommendation | null;
  isFromCache?: boolean;
  lastUpdated?: Date | null;
  onNavigate?: (station: Station) => void;
}

export function RecommendationCard({ recommendation, isFromCache, lastUpdated, onNavigate }: Props) {
  if (!recommendation) {
    return (
      <View style={[styles.card, styles.greenCard]}>
        <Text style={styles.checkmark}>✓</Text>
        <Text style={styles.okTitle}>All Good</Text>
        <Text style={styles.okSubtitle}>No charging needed right now</Text>
        {lastUpdated && (
          <Text style={styles.lastUpdated}>
            Updated {formatRelative(lastUpdated)}
          </Text>
        )}
      </View>
    );
  }

  const station = recommendation.recommended_station;

  return (
    <View style={[styles.card, styles.alertCard]}>
      {isFromCache && (
        <View style={styles.cacheBanner}>
          <Text style={styles.cacheText}>
            Offline — last updated {lastUpdated ? formatRelative(lastUpdated) : "unknown"}
          </Text>
        </View>
      )}

      <View style={styles.header}>
        <Text style={styles.alertIcon}>⚡</Text>
        <Text style={styles.alertTitle}>Charging Needed</Text>
      </View>

      <View style={styles.socRow}>
        <Text style={styles.socValue}>{recommendation.trigger_soc.toFixed(0)}%</Text>
        <Text style={styles.socLabel}>SoC · {recommendation.estimated_range_km.toFixed(0)} km range</Text>
      </View>

      {station && (
        <View style={styles.stationBox}>
          <Text style={styles.stationName}>{station.name}</Text>
          <View style={styles.stationMeta}>
            <Text style={styles.stationMetaText}>{station.distance_km.toFixed(1)} km away</Text>
            <Text style={styles.dot}>·</Text>
            <Text style={styles.stationMetaText}>{station.available_connectors} available</Text>
            <Text style={styles.dot}>·</Text>
            <Text style={styles.stationMetaText}>₹{station.price_per_kwh_inr}/kWh</Text>
          </View>

          {onNavigate && (
            <TouchableOpacity
              style={styles.navigateBtn}
              onPress={() => onNavigate(station)}
              accessibilityLabel={`Navigate to ${station.name}`}
            >
              <Text style={styles.navigateBtnText}>Navigate →</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
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
  card: {
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  greenCard: {
    backgroundColor: "#052e16",
    borderWidth: 1,
    borderColor: "#14532d",
    alignItems: "center",
    paddingVertical: 24,
  },
  alertCard: {
    backgroundColor: "#451a03",
    borderWidth: 1,
    borderColor: "#92400e",
  },
  cacheBanner: {
    backgroundColor: "#1e293b",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 12,
  },
  cacheText: {
    color: "#94a3b8",
    fontSize: 12,
    textAlign: "center",
  },
  checkmark: {
    fontSize: 32,
    color: "#10B981",
    marginBottom: 8,
  },
  okTitle: {
    color: "#10B981",
    fontSize: 18,
    fontWeight: "700",
  },
  okSubtitle: {
    color: "#6ee7b7",
    fontSize: 13,
    marginTop: 4,
  },
  lastUpdated: {
    color: "#374151",
    fontSize: 11,
    marginTop: 8,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  alertIcon: {
    fontSize: 20,
  },
  alertTitle: {
    color: "#fbbf24",
    fontSize: 16,
    fontWeight: "700",
  },
  socRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginBottom: 16,
  },
  socValue: {
    color: "#ef4444",
    fontSize: 36,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
  socLabel: {
    color: "#fca5a5",
    fontSize: 14,
  },
  stationBox: {
    backgroundColor: "rgba(0,0,0,0.3)",
    borderRadius: 10,
    padding: 12,
  },
  stationName: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 4,
  },
  stationMeta: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 4,
    marginBottom: 12,
  },
  stationMetaText: {
    color: "#fde68a",
    fontSize: 12,
  },
  dot: {
    color: "#92400e",
    fontSize: 12,
  },
  navigateBtn: {
    backgroundColor: "#3B82F6",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
  },
  navigateBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 14,
  },
});
