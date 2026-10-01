import { create } from 'zustand'
import { supabase } from '@/lib/supabase'
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
  logout: async () => {
    await supabase.auth.signOut()
    set({ user: null, workspace: null, isAuthenticated: false })
  },
}))
