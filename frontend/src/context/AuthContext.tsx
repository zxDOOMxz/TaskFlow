import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { User, Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/auth'

interface AuthContextValue {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => ReturnType<typeof supabase.auth.signInWithPassword>
  signUp: (email: string, password: string, firstName: string, lastName: string) => ReturnType<typeof supabase.auth.signUp>
  signOut: () => ReturnType<typeof supabase.auth.signOut>
  resetPassword: (email: string) => ReturnType<typeof supabase.auth.resetPasswordForEmail>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const { setUser: setStoreUser, logout: storeLogout } = useAuthStore()

  const loadProfile = useCallback(async (currentSession: Session | null) => {
    if (!currentSession) {
      setStoreUser(null)
      return
    }
    try {
      const { data } = await authApi.me()
      setStoreUser(data)
    } catch (err) {
      console.error('Failed to load profile:', err)
      setStoreUser(null)
    }
  }, [setStoreUser])

  useEffect(() => {
    let active = true

    const timeout = setTimeout(() => {
      if (!active) return
      console.warn('Supabase getSession timed out')
      setLoading(false)
    }, 5000)

    supabase.auth.getSession().then(({ data, error }) => {
      clearTimeout(timeout)
      if (!active) return
      if (error) console.error('getSession error:', error)
      setSession(data.session)
      setUser(data.session?.user ?? null)
      loadProfile(data.session)
      setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setUser(nextSession?.user ?? null)
      loadProfile(nextSession)
      if (!nextSession) {
        storeLogout()
      }
    })

    return () => {
      active = false
      clearTimeout(timeout)
      listener.subscription.unsubscribe()
    }
  }, [loadProfile, storeLogout])

  const signIn = useCallback(
    (email: string, password: string) =>
      supabase.auth.signInWithPassword({ email, password }),
    []
  )

  const signUp = useCallback(
    (email: string, password: string, firstName: string, lastName: string) =>
      supabase.auth.signUp({
        email,
        password,
        options: {
          data: { first_name: firstName, last_name: lastName },
        },
      }),
    []
  )

  const signOut = useCallback(async () => {
    const result = await supabase.auth.signOut()
    storeLogout()
    return result
  }, [storeLogout])

  const resetPassword = useCallback(
    (email: string) =>
      supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/login`,
      }),
    []
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      session,
      loading,
      signIn,
      signUp,
      signOut,
      resetPassword,
    }),
    [user, session, loading, signIn, signUp, signOut, resetPassword]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function useSession() {
  const { session } = useAuth()
  return session
}

export function useIsAuthenticated() {
  const { session, loading } = useAuth()
  return { isAuthenticated: !!session, loading }
}
