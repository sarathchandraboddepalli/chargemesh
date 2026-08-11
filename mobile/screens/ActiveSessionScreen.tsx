import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { driverApi } from "../services/api";

interface Session {
  id: string;
  station_name: string;
  network_name: string;
  energy_delivered_kwh: number;
  started_at: string;
  connector_id: number;
  status: string;
}

export function ActiveSessionScreen() {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStopping, setIsStopping] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    loadSession();
    const interval = setInterval(loadSession, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!session?.started_at) return;
    const start = new Date(session.started_at).getTime();
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [session?.started_at]);

  const loadSession = async () => {
    try {
      const { data } = await driverApi.getActiveSession();
      setSession(data);
    } catch {
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    Alert.alert(
      "Stop Charging?",
      "Are you sure you want to end this charging session?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Stop",
          style: "destructive",
          onPress: async () => {
            setIsStopping(true);
            try {
              await driverApi.stopSession();
              setSession(null);
              Alert.alert("Session Ended", "Your charging session has been stopped.");
            } catch (err: any) {
              Alert.alert("Error", err?.response?.data?.detail ?? "Failed to stop session");
            } finally {
              setIsStopping(false);
            }
          },
        },
      ]
    );
  };

  const formatElapsed = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#3B82F6" size="large" />
      </View>
    );
  }

  if (!session) {
    return (
      <View style={styles.noSessionContainer}>
        <Text style={styles.noSessionIcon}>🔌</Text>
        <Text style={styles.noSessionTitle}>No Active Session</Text>
        <Text style={styles.noSessionSubtitle}>
          Go to Stations to find and start a charging session
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Charging Active</Text>
        <View style={styles.liveIndicator}>
          <View style={styles.liveDot} />
          <Text style={styles.liveText}>Live</Text>
        </View>
      </View>

      {/* Session card */}
      <View style={styles.sessionCard}>
        <Text style={styles.stationName}>{session.station_name}</Text>
        <Text style={styles.networkName}>{session.network_name}</Text>

        <View style={styles.metricsRow}>
          <View style={styles.metric}>
            <Text style={styles.metricValue}>{formatElapsed(elapsed)}</Text>
            <Text style={styles.metricLabel}>Duration</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricValue}>
              {session.energy_delivered_kwh?.toFixed(2)} kWh
            </Text>
            <Text style={styles.metricLabel}>Energy</Text>
          </View>
          <View style={styles.metricDivider} />
          <View style={styles.metric}>
            <Text style={styles.metricValue}>#{session.connector_id}</Text>
            <Text style={styles.metricLabel}>Connector</Text>
          </View>
        </View>
      </View>

      {/* Stop button */}
      <TouchableOpacity
        style={[styles.stopBtn, isStopping && styles.stopBtnDisabled]}
        onPress={handleStop}
        disabled={isStopping}
      >
        {isStopping ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.stopBtnText}>Stop Charging</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  content: {
    padding: 20,
    paddingTop: 60,
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0f172a",
  },
  noSessionContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0f172a",
    padding: 32,
  },
  noSessionIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  noSessionTitle: {
    color: "#94a3b8",
    fontSize: 20,
    fontWeight: "600",
    marginBottom: 8,
  },
  noSessionSubtitle: {
    color: "#64748b",
    fontSize: 14,
    textAlign: "center",
    lineHeight: 20,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  title: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
  },
  liveIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#10B98120",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  liveDot: {
    width: 7,
    height: 7,
    backgroundColor: "#10B981",
    borderRadius: 4,
  },
  liveText: {
    color: "#10B981",
    fontSize: 12,
    fontWeight: "600",
  },
  sessionCard: {
    backgroundColor: "#1e293b",
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: "#334155",
    marginBottom: 24,
  },
  stationName: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 4,
  },
  networkName: {
    color: "#64748b",
    fontSize: 13,
    marginBottom: 20,
  },
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  metric: {
    flex: 1,
    alignItems: "center",
  },
  metricValue: {
    color: "#3B82F6",
    fontSize: 18,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
    marginBottom: 4,
  },
  metricLabel: {
    color: "#64748b",
    fontSize: 11,
  },
  metricDivider: {
    width: 1,
    backgroundColor: "#334155",
    marginVertical: 4,
  },
  stopBtn: {
    backgroundColor: "#ef4444",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  stopBtnDisabled: {
    opacity: 0.6,
  },
  stopBtnText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
});
