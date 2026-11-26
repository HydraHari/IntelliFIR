// types/auth.ts
export interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'officer' | 'reviewer'
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
  role: 'admin' | 'officer' | 'reviewer'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}
