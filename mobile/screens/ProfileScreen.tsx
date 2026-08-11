import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from "react-native";

interface Props {
  user: { email: string; phone?: string; role: string } | null;
  onLogout: () => void;
}

export function ProfileScreen({ user, onLogout }: Props) {
  const handleLogout = () => {
    Alert.alert(
      "Sign Out",
      "Are you sure you want to sign out?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Sign Out", style: "destructive", onPress: onLogout },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
      </View>

      {/* Avatar */}
      <View style={styles.avatarContainer}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {user?.email?.[0]?.toUpperCase() ?? "D"}
          </Text>
        </View>
        <Text style={styles.email}>{user?.email ?? "—"}</Text>
        {user?.phone && <Text style={styles.phone}>{user.phone}</Text>}
        <View style={styles.roleBadge}>
          <Text style={styles.roleText}>{user?.role ?? "driver"}</Text>
        </View>
      </View>

      {/* Info rows */}
      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>App Version</Text>
          <Text style={styles.rowValue}>1.0.0</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.rowLabel}>Mode</Text>
          <Text style={styles.rowValue}>Mock OEM</Text>
        </View>
      </View>

      {/* Privacy notice */}
      <View style={styles.privacyBox}>
        <Text style={styles.privacyTitle}>Privacy</Text>
        <Text style={styles.privacyText}>
          ChargeMesh does NOT track your GPS location. Your device location is used only to
          find nearby charging stations and is never transmitted to or stored by our servers.
          Vehicle location data comes exclusively from manufacturer (OEM) telemetry systems.
        </Text>
      </View>

      {/* Sign out */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutBtnText}>Sign Out</Text>
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
  header: {
    marginBottom: 24,
  },
  title: {
    color: "#fff",
    fontSize: 22,
    fontWeight: "700",
  },
  avatarContainer: {
    alignItems: "center",
    marginBottom: 28,
  },
  avatar: {
    width: 72,
    height: 72,
    backgroundColor: "#1d4ed8",
    borderRadius: 36,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  avatarText: {
    color: "#fff",
    fontSize: 28,
    fontWeight: "700",
  },
  email: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
  },
  phone: {
    color: "#64748b",
    fontSize: 14,
    marginBottom: 8,
  },
  roleBadge: {
    backgroundColor: "#1e40af20",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: "#1e40af",
  },
  roleText: {
    color: "#60a5fa",
    fontSize: 12,
    fontWeight: "600",
    textTransform: "capitalize",
  },
  section: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    marginBottom: 16,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  rowLabel: {
    color: "#94a3b8",
    fontSize: 14,
  },
  rowValue: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
  privacyBox: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#334155",
    marginBottom: 24,
  },
  privacyTitle: {
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  privacyText: {
    color: "#64748b",
    fontSize: 12,
    lineHeight: 18,
  },
  logoutBtn: {
    backgroundColor: "#1e293b",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#ef4444",
  },
  logoutBtnText: {
    color: "#ef4444",
    fontSize: 16,
    fontWeight: "700",
  },
});
