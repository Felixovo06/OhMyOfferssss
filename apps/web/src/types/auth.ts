export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  user: User
  access_token: string
  token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}
