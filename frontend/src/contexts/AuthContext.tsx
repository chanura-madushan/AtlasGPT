import { createContext, useEffect, useState, type ReactNode } from 'react'
import { authApi } from '../services/api'
import type { User } from '../types'

export interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  continueAsGuest: () => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    authApi.me().then((currentUser) => {
      if (active) setUser(currentUser)
    }).catch(() => {
      if (active) setUser(null)
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [])

  async function login(email: string, password: string) {
    await authApi.login(email, password)
    setUser(await authApi.me())
  }

  async function register(email: string, password: string) {
    await authApi.register(email, password)
    await login(email, password)
  }

  async function continueAsGuest() {
    await authApi.guest()
    setUser(await authApi.me())
  }

  async function logout() {
    await authApi.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated: user !== null, login, register, continueAsGuest, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
