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

  useEffect(() => {
    let active = true

    supabase.auth.getSession().then(({ data, error }) => {
      if (!active) return
      if (error) console.error('getSession error:', error)
      setSession(data.session)
      setUser(data.session?.user ?? null)
      setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setUser(nextSession?.user ?? null)
    })

    return () => {
      active = false
      listener.subscription.unsubscribe()
    }
  }, [])

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

  const signOut = useCallback(() => supabase.auth.signOut(), [])

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
