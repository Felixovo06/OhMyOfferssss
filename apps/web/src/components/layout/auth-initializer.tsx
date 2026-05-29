"use client"

import { useEffect } from "react"
import { getMe } from "@/lib/api/auth"
import { useAuthStore } from "@/lib/store/auth"

/**
 * Restores auth from localStorage and validates it with the backend.
 */
export function AuthInitializer() {
  useEffect(() => {
    let cancelled = false

    async function restoreAuth() {
      const { clearAuth, restoreToken, setLoading, setUser } = useAuthStore.getState()

      const token = localStorage.getItem("auth_token")
      if (token) {
        restoreToken(token)
        try {
          const user = await getMe()
          if (!cancelled) setUser(user)
        } catch {
          if (!cancelled) clearAuth()
        }
      } else {
        setLoading(false)
      }
    }

    restoreAuth()

    return () => {
      cancelled = true
    }
  }, [])

  return null
}
