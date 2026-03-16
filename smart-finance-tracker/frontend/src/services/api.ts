/**
 * frontend/src/services/api.ts
 * Centralised Axios instance with JWT interceptors
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: BASE_URL, timeout: 15_000 });

// ── Request — attach access token ─────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response — refresh on 401 ────────────────────────────────
let refreshing = false;
api.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const orig = err.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (err.response?.status === 401 && !orig._retry && !refreshing) {
      orig._retry = true;
      refreshing  = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem("access_token",  data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          orig.headers!.Authorization = `Bearer ${data.access_token}`;
          refreshing = false;
          return api(orig);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
      refreshing = false;
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────────
export const authApi = {
  register: (p: { email: string; password: string; full_name: string; currency: string }) =>
    api.post("/auth/register", p),
  login:  (p: { email: string; password: string }) => api.post("/auth/login", p),
  me:     () => api.get("/auth/me"),
};

// ── Transactions ─────────────────────────────────────────────
export const txApi = {
  list:   (params?: object) => api.get("/transactions", { params }),
  create: (p: object)       => api.post("/transactions", p),
  update: (id: string, p: object) => api.patch(`/transactions/${id}`, p),
  remove: (id: string)      => api.delete(`/transactions/${id}`),
};

// ── Analytics ────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: (month: number, year: number) => api.get("/analytics/dashboard", { params: { month, year } }),
  insights:  () => api.get("/analytics/insights"),
};

// ── Budgets ──────────────────────────────────────────────────
export const budgetsApi = {
  list:   (month: number, year: number) => api.get("/budgets", { params: { month, year } }),
  create: (p: object) => api.post("/budgets", p),
  remove: (id: string) => api.delete(`/budgets/${id}`),
};

// ── Categories ───────────────────────────────────────────────
export const categoriesApi = { list: () => api.get("/categories") };

// ── Export ───────────────────────────────────────────────────
export const exportApi = {
  csv: (start?: string, end?: string) =>
    api.get("/export/csv", { params: { start_date: start, end_date: end }, responseType: "blob" }),
  importCsv: (file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return api.post("/export/csv", fd, { headers: { "Content-Type": "multipart/form-data" } });
  },
};
