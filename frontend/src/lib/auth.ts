import Cookies from "js-cookie";
import api from "./api";
import { User } from "@/types";

export async function register(email: string, password: string): Promise<User> {
  const res = await api.post("/auth/register", { email, password });
  return res.data;
}

export async function login(
  email: string,
  password: string
): Promise<{ access_token: string }> {
  const res = await api.post("/auth/login", { email, password });
  const { access_token } = res.data;
  Cookies.set("token", access_token, { expires: 1, sameSite: "Strict" });
  return res.data;
}

export async function logout() {
  Cookies.remove("token");
}

export async function getMe(): Promise<User> {
  const res = await api.get("/auth/me");
  return res.data;
}

export async function regenerateApiKey(): Promise<User> {
  const res = await api.post("/auth/regenerate-key");
  return res.data;
}

export function isAuthenticated(): boolean {
  return !!Cookies.get("token");
}
