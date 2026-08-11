import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
} from "react-native";
import { driverApi } from "../services/api";

export function SwapScreen() {
  const [batteryId, setBatteryId] = useState("");
  const [kwhConsumed, setKwhConsumed] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleReport = async () => {
    if (!batteryId.trim()) {
      Alert.alert("Missing Info", "Please scan or enter the battery serial number.");
      return;
    }
    const kwh = parseFloat(kwhConsumed);
    if (isNaN(kwh) || kwh < 0) {
      Alert.alert("Invalid Input", "Please enter valid kWh consumed.");
      return;
    }

    Alert.alert(
      "Confirm Swap Report",
      `Battery: ${batteryId}\nkWh consumed: ${kwh.toFixed(2)}`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Submit",
          onPress: async () => {
            setIsSubmitting(true);
            try {
              await driverApi.reportSwap(batteryId.trim(), kwh);
              Alert.alert(
                "Swap Reported",
                "The battery swap has been recorded and will be included in the next settlement.",
                [{ text: "OK", onPress: () => { setBatteryId(""); setKwhConsumed(""); } }]
              );
            } catch (err: any) {
              Alert.alert("Error", err?.response?.data?.detail ?? "Failed to report swap");
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Report Battery Swap</Text>
        <Text style={styles.subtitle}>
          Record a battery swap for BaaS settlement
        </Text>
      </View>

      <View style={styles.form}>
        <View style={styles.field}>
          <Text style={styles.label}>Battery Serial Number</Text>
          <Text style={styles.hint}>Scan the QR code on the battery or enter manually</Text>
          <TextInput
            style={styles.input}
            value={batteryId}
            onChangeText={setBatteryId}
            placeholder="e.g. SUN-BAT-00123"
            placeholderTextColor="#475569"
            autoCapitalize="characters"
            autoCorrect={false}
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Energy Consumed (kWh)</Text>
          <Text style={styles.hint}>From the battery display or station meter</Text>
          <TextInput
            style={styles.input}
            value={kwhConsumed}
            onChangeText={setKwhConsumed}
            placeholder="e.g. 3.45"
            placeholderTextColor="#475569"
            keyboardType="decimal-pad"
          />
        </View>

        {/* Settlement formula note */}
        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>BaaS Settlement Formula</Text>
          <Text style={styles.infoText}>
            kWh Cost = consumed × ₹/kWh (per your agreement){"\n"}
            Degradation Cost = excess SoH loss × ₹/SoH point{"\n"}
            Total = kWh Cost + Degradation Cost
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.submitBtn, isSubmitting && styles.submitBtnDisabled]}
          onPress={handleReport}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitBtnText}>Report Swap</Text>
          )}
        </TouchableOpacity>
      </View>
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
    marginBottom: 4,
  },
  subtitle: {
    color: "#64748b",
    fontSize: 14,
  },
  form: {
    gap: 20,
  },
  field: {
    gap: 4,
  },
  label: {
    color: "#94a3b8",
    fontSize: 14,
    fontWeight: "600",
  },
  hint: {
    color: "#64748b",
    fontSize: 11,
  },
  input: {
    backgroundColor: "#1e293b",
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: "#fff",
    fontSize: 15,
    marginTop: 6,
  },
  infoBox: {
    backgroundColor: "#1e293b",
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: "#334155",
  },
  infoTitle: {
    color: "#94a3b8",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 6,
  },
  infoText: {
    color: "#64748b",
    fontSize: 12,
    lineHeight: 18,
    fontVariant: ["tabular-nums"],
  },
  submitBtn: {
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 8,
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
});
