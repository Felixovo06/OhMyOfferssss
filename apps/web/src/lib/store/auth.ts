import { create } from "zustand"
import type { User } from "@/types/auth"
import { api } from "@/lib/api/client"

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  setAuth: (user: User, token: string) => void
  restoreToken: (token: string) => void
  setUser: (user: User) => void
  setLoading: (loading: boolean) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: true,
  setAuth: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token)
    }
    set({ user, token, isLoading: false })
  },
  restoreToken: (token) => set({ token, isLoading: true }),
  setUser: (user) => set({ user, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  clearAuth: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token")
    }
    set({ user: null, token: null, isLoading: false })
  },
}))

api.setTokenGetter(() => useAuthStore.getState().token)
