import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { driverApi } from "../services/api";

interface Session {
  id: string;
  station_name: string;
  network_name: string;
  energy_delivered_kwh: number;
  total_cost_inr: number;
  started_at: string;
  ended_at: string;
  status: string;
}

function formatRelative(dateStr: string) {
  const date = new Date(dateStr);
  const diffMs = Date.now() - date.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function getDuration(start: string, end: string) {
  const diffMin = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60000);
  if (diffMin < 60) return `${diffMin} min`;
  return `${Math.floor(diffMin / 60)}h ${diffMin % 60}m`;
}

export function HistoryScreen() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    driverApi
      .getHistory(50)
      .then(({ data }) => setSessions(data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#3B82F6" size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Session History</Text>
        <Text style={styles.subtitle}>{sessions.length} sessions</Text>
      </View>

      <FlatList
        data={sessions}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={() => (
          <View style={styles.center}>
            <Text style={styles.emptyText}>No sessions yet</Text>
          </View>
        )}
        renderItem={({ item }) => (
          <View style={styles.sessionCard}>
            <View style={styles.cardHeader}>
              <Text style={styles.stationName}>{item.station_name}</Text>
              <Text style={styles.date}>{formatRelative(item.started_at)}</Text>
            </View>
            <Text style={styles.network}>{item.network_name}</Text>

            <View style={styles.metricsRow}>
              <View style={styles.metric}>
                <Text style={styles.metricValue}>
                  {item.energy_delivered_kwh?.toFixed(2)} kWh
                </Text>
                <Text style={styles.metricLabel}>Energy</Text>
              </View>
              <View style={styles.metric}>
                {item.started_at && item.ended_at ? (
                  <Text style={styles.metricValue}>
                    {getDuration(item.started_at, item.ended_at)}
                  </Text>
                ) : (
                  <Text style={styles.metricValue}>—</Text>
                )}
                <Text style={styles.metricLabel}>Duration</Text>
              </View>
              <View style={styles.metric}>
                <Text style={styles.metricValue}>
                  {item.total_cost_inr != null ? `₹${item.total_cost_inr.toFixed(0)}` : "—"}
                </Text>
                <Text style={styles.metricLabel}>Cost</Text>
              </View>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  header: {
    paddingHorizontal: 20,
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
  list: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyText: {
    color: "#64748b",
    fontSize: 14,
  },
  sessionCard: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 4,
  },
  stationName: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
    flex: 1,
    marginRight: 8,
  },
  date: {
    color: "#64748b",
    fontSize: 12,
  },
  network: {
    color: "#64748b",
    fontSize: 12,
    marginBottom: 12,
  },
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
  },
  metric: {
    alignItems: "center",
  },
  metricValue: {
    color: "#3B82F6",
    fontSize: 14,
    fontWeight: "600",
    fontVariant: ["tabular-nums"],
    marginBottom: 2,
  },
  metricLabel: {
    color: "#64748b",
    fontSize: 11,
  },
});
