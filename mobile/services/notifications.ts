import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import { driverApi } from "./api";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("[ChargeMesh] Push notification permission denied");
    return null;
  }

  const tokenData = await Notifications.getExpoPushTokenAsync();
  const token = tokenData.data;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("chargemesh", {
      name: "ChargeMesh Alerts",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#3B82F6",
    });

    await Notifications.setNotificationChannelAsync("thermal", {
      name: "Thermal Alerts",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 500, 250, 500],
      lightColor: "#EF4444",
    });
  }

  // Register token with backend
  try {
    await driverApi.updatePushToken(token);
  } catch (err) {
    console.log("[ChargeMesh] Failed to register push token:", err);
  }

  return token;
}

export function scheduleLocalNotification(title: string, body: string) {
  Notifications.scheduleNotificationAsync({
    content: { title, body, sound: true },
    trigger: null,
  });
}
