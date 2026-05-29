import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getMe, login, logout, register } from "@/lib/api/auth"
import { useAuthStore } from "@/lib/store/auth"
import type { LoginRequest, RegisterRequest } from "@/types/auth"

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: LoginRequest) => login(data),
    onSuccess: (res) => {
      setAuth(res.user, res.token)
      queryClient.invalidateQueries({ queryKey: ["me"] })
    },
  })
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth)

  return useMutation({
    mutationFn: (data: RegisterRequest) => register(data),
    onSuccess: (res) => {
      setAuth(res.user, res.token)
    },
  })
}

export function useLogout() {
  const clearAuth = useAuthStore((s) => s.clearAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => logout(),
    onSuccess: () => {
      clearAuth()
      queryClient.clear()
    },
  })
}

export function useMe() {
  const { token, setUser } = useAuthStore()

  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const user = await getMe()
      setUser(user)
      return user
    },
    enabled: !!token,
    retry: false,
    staleTime: 60 * 1000,
  })
}
