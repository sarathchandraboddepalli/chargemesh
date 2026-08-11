/**
 * ChargeMesh Driver App
 *
 * React Native (Expo) driver companion for ChargeMesh EV Infrastructure OS.
 *
 * SECURITY: This app does NOT send GPS coordinates to the backend for storage.
 * Location is used only client-side to sort nearby stations by distance.
 * Vehicle position data comes exclusively from OEM telemetry (server-side).
 */

import React, { useEffect } from "react";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Text } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { HomeScreen } from "./screens/HomeScreen";
import { StationsScreen } from "./screens/StationsScreen";
import { ActiveSessionScreen } from "./screens/ActiveSessionScreen";
import { HistoryScreen } from "./screens/HistoryScreen";
import { SwapScreen } from "./screens/SwapScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { LoginScreen } from "./screens/LoginScreen";
import { useAuthState } from "./hooks/useAuth";
import { registerForPushNotificationsAsync } from "./services/notifications";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      retry: 2,
    },
  },
});

const DARK_THEME = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    background: "#0f172a",
    card: "#1e293b",
    text: "#ffffff",
    border: "#334155",
    notification: "#3B82F6",
    primary: "#3B82F6",
  },
};

function TabIcon({ icon, focused }: { icon: string; focused: boolean }) {
  return (
    <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.5 }}>{icon}</Text>
  );
}

function MainTabs({ user, onLogout }: { user: any; onLogout: () => void }) {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: "#1e293b",
          borderTopColor: "#334155",
        },
        tabBarActiveTintColor: "#3B82F6",
        tabBarInactiveTintColor: "#64748b",
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="⚡" focused={focused} />,
          tabBarLabel: "Home",
        }}
      />
      <Tab.Screen
        name="Stations"
        component={StationsScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="🔌" focused={focused} />,
          tabBarLabel: "Stations",
        }}
      />
      <Tab.Screen
        name="Session"
        component={ActiveSessionScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="⏱" focused={focused} />,
          tabBarLabel: "Session",
        }}
      />
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="📋" focused={focused} />,
          tabBarLabel: "History",
        }}
      />
      <Tab.Screen
        name="Swap"
        component={SwapScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="🔋" focused={focused} />,
          tabBarLabel: "Swap",
        }}
      />
      <Tab.Screen
        name="Profile"
        options={{
          tabBarIcon: ({ focused }) => <TabIcon icon="👤" focused={focused} />,
          tabBarLabel: "Profile",
        }}
      >
        {() => <ProfileScreen user={user} onLogout={onLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

function AppNavigator() {
  const { user, isLoading, login, logout } = useAuthState();
  const [loginError, setLoginError] = React.useState<string | null>(null);

  useEffect(() => {
    if (user) {
      registerForPushNotificationsAsync().catch(console.warn);
    }
  }, [user]);

  const handleLogin = async (email: string, password: string) => {
    setLoginError(null);
    try {
      await login(email, password);
    } catch (err: any) {
      setLoginError(err?.response?.data?.detail ?? "Invalid credentials");
    }
  };

  if (isLoading) {
    return null; // Splash screen shows
  }

  return (
    <NavigationContainer theme={DARK_THEME}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <Stack.Screen name="Main">
            {() => <MainTabs user={user} onLogout={logout} />}
          </Stack.Screen>
        ) : (
          <Stack.Screen name="Login">
            {() => <LoginScreen onLogin={handleLogin} error={loginError} />}
          </Stack.Screen>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <AppNavigator />
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
