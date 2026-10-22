import { create } from 'zustand'
import { User, Workspace } from '@/types'

interface AuthState {
  user: User | null
  workspace: Workspace | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User | null) => void
  setWorkspace: (workspace: Workspace | null) => void
  setLoading: (loading: boolean) => void
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  workspace: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setWorkspace: (workspace) => set({ workspace }),
  setLoading: (loading) => set({ isLoading: loading }),
  // Чистит только локальное состояние. Вызывать supabase.auth.signOut() отсюда нельзя:
  // logout используется внутри onAuthStateChange, а auth-методы Supabase внутри
  // этого обработчика приводят к рекурсии/дедлоку (страница зависает).
  logout: async () => {
    set({ user: null, workspace: null, isAuthenticated: false })
  },
}))
