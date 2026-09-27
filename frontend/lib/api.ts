import axios from "axios";
import Cookies from "js-cookie";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface CreditBalance {
  balance: number;
  updated_at: string;
}

export interface VideoJob {
  id: string;
  prompt: string;
  format: string;
  status: string;
  progress_percent: number;
  output_url: string | null;
  error_message: string | null;
  created_at: string;
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  Cookies.set("access_token", data.access_token, { expires: 1 });
  Cookies.set("refresh_token", data.refresh_token, { expires: 7 });
  return data;
}

export async function register(email: string, password: string, full_name: string) {
  const { data } = await api.post("/auth/register", { email, password, full_name });
  return data;
}

export async function getMe() {
  const { data } = await api.get("/users/me");
  return data;
}

export async function getCreditBalance(): Promise<CreditBalance> {
  const { data } = await api.get("/credits/balance");
  return data;
}

export async function createTopUpCheckout(packageId: string) {
  const { data } = await api.post("/credits/top-up/checkout", { package_id: packageId });
  return data;
}

export async function listVideoJobs(): Promise<VideoJob[]> {
  const { data } = await api.get("/videos/jobs");
  return data;
}

export async function createVideoJob(prompt: string, format: string): Promise<VideoJob> {
  const { data } = await api.post("/videos/jobs", { prompt, format });
  return data;
}

export function logout() {
  Cookies.remove("access_token");
  Cookies.remove("refresh_token");
}
