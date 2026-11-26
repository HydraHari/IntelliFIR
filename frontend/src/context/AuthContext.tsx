import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../api/auth'
import type { User, LoginRequest, RegisterRequest } from '../types/auth'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('auth_user')
    return saved ? JSON.parse(saved) : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'))
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken) {
        try {
          const userData = await authApi.me()
          setUser(userData)
          localStorage.setItem('auth_user', JSON.stringify(userData))
        } catch (err) {
          console.error('Failed to restore session:', err)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
          setToken(null)
          setUser(null)
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [])

  const login = async (data: LoginRequest) => {
    const resp = await authApi.login(data)
    setToken(resp.access_token)
    setUser(resp.user)
    localStorage.setItem('auth_token', resp.access_token)
    localStorage.setItem('auth_user', JSON.stringify(resp.user))
  }

  const register = async (data: RegisterRequest) => {
    await authApi.register(data)
    await login({ email: data.email, password: data.password })
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore network errors on logout
    } finally {
      setToken(null)
      setUser(null)
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      window.location.href = '/login'
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
