/**
 * store/authStore.ts — Zustand auth state with persistence
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi } from "../services/api";

export interface User {
  id: string;
  email: string;
  full_name: string;
  currency: string;
  monthly_income: number;
}

interface AuthState {
  user: User | null;
  isAuth: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string, currency: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuth: false,
      loading: false,
      error: null,

      login: async (email, password) => {
        set({ loading: true, error: null });
        try {
          const { data } = await authApi.login({ email, password });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          set({ user: data.user, isAuth: true, loading: false });
        } catch (e: any) {
          set({ error: e.response?.data?.detail ?? "Login failed", loading: false });
        }
      },

      register: async (email, password, full_name, currency) => {
        set({ loading: true, error: null });
        try {
          const { data } = await authApi.register({ email, password, full_name, currency });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          set({ user: data.user, isAuth: true, loading: false });
        } catch (e: any) {
          set({ error: e.response?.data?.detail ?? "Registration failed", loading: false });
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuth: false });
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-store",
      partialize: (s) => ({ user: s.user, isAuth: s.isAuth }),
    }
  )
);
