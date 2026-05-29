import { api } from "./client"
import type { LoginRequest, LoginResponse, User, RegisterRequest } from "@/types/auth"

export function login(data: LoginRequest) {
  return api.post<LoginResponse>("/api/v1/auth/login", data)
}

export function logout() {
  return api.post<void>("/api/v1/auth/logout")
}

export function getMe() {
  return api.get<User>("/api/v1/auth/me")
}

export function register(data: RegisterRequest) {
  return api.post<LoginResponse>("/api/v1/auth/register", data)
}
