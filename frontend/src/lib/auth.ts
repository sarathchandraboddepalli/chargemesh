import Cookies from "js-cookie";
import { api } from "./api";

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  Cookies.set("access_token", data.access_token, { expires: 1 / 96 });
  Cookies.set("refresh_token", data.refresh_token, { expires: 30 });
  return data;
}

export async function register(email: string, password: string, fullName?: string) {
  const { data } = await api.post("/auth/register", { email, password, full_name: fullName });
  Cookies.set("access_token", data.access_token, { expires: 1 / 96 });
  Cookies.set("refresh_token", data.refresh_token, { expires: 30 });
  return data;
}

export function logout() {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
  window.location.href = "/auth/login";
}

export function isAuthenticated(): boolean {
  return !!Cookies.get("access_token");
}
