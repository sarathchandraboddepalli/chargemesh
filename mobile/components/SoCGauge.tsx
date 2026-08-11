import React from "react";
import { View, Text, StyleSheet } from "react-native";
import Svg, { Circle, G } from "react-native-svg";

interface Props {
  soc: number | null;
  size?: number;
}

export function SoCGauge({ soc, size = 160 }: Props) {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = soc != null ? Math.min(100, Math.max(0, soc)) : 0;
  const strokeDashoffset = circumference * (1 - progress / 100);

  const color =
    soc == null ? "#64748b"
    : soc > 40 ? "#10B981"
    : soc > 20 ? "#F59E0B"
    : "#EF4444";

  return (
    <View style={styles.container}>
      <Svg width={size} height={size}>
        <G rotation="-90" origin={`${size / 2},${size / 2}`}>
          {/* Background ring */}
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1e293b"
            strokeWidth={12}
            fill="none"
          />
          {/* Progress ring */}
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={12}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </G>
      </Svg>

      {/* Center text */}
      <View style={StyleSheet.absoluteFillObject}>
        <View style={styles.center}>
          <Text style={[styles.socValue, { color }]}>
            {soc != null ? `${soc.toFixed(1)}%` : "—"}
          </Text>
          <Text style={styles.socLabel}>State of Charge</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "relative",
    alignItems: "center",
    justifyContent: "center",
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  socValue: {
    fontSize: 28,
    fontWeight: "700",
    fontVariant: ["tabular-nums"],
  },
  socLabel: {
    fontSize: 12,
    color: "#64748b",
    marginTop: 2,
  },
});
