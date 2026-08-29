import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../services/api'
import type { Role, UserSummary } from '../types'

interface AuthContextValue {
  user: UserSummary | null
  token: string | null
  isLoading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => void
  hasRole: (...roles: Role[]) => boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSummary | null>(() => {
    const cached = localStorage.getItem('stat-growth-user')
    return cached ? JSON.parse(cached) as UserSummary : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('stat-growth-token'))
  const [isLoading, setIsLoading] = useState(Boolean(token))

  useEffect(() => {
    if (!token) {
      setIsLoading(false)
      return
    }
    api.me()
      .then((current) => {
        setUser(current)
        localStorage.setItem('stat-growth-user', JSON.stringify(current))
      })
      .catch(() => {
        localStorage.removeItem('stat-growth-token')
        localStorage.removeItem('stat-growth-user')
        setToken(null)
        setUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [token])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    isLoading,
    signIn: async (email, password) => {
      const result = await api.login(email, password)
      localStorage.setItem('stat-growth-token', result.access_token)
      localStorage.setItem('stat-growth-user', JSON.stringify(result.user))
      setToken(result.access_token)
      setUser(result.user)
    },
    signOut: () => {
      localStorage.removeItem('stat-growth-token')
      localStorage.removeItem('stat-growth-user')
      setToken(null)
      setUser(null)
    },
    hasRole: (...roles) => Boolean(user && roles.includes(user.role)),
  }), [isLoading, token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
