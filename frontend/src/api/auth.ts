// api/auth.ts
import apiClient from './client'
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth'

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<AuthResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    apiClient.post<User>('/auth/register', data).then((r) => r.data),

  me: () => apiClient.get<User>('/auth/me').then((r) => r.data),

  logout: () => apiClient.post('/auth/logout').then((r) => r.data),
}
