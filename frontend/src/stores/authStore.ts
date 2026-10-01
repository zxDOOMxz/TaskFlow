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
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  workspace: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: true,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setWorkspace: (workspace) => set({ workspace }),
  setLoading: (loading) => set({ isLoading: loading }),
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, workspace: null, isAuthenticated: false })
  },
}))
