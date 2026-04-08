import { create } from 'zustand'

interface User {
  id: string
  email: string
  name: string
  avatarUrl: string
  authProvider: 'google' | 'x'
  tier: 'free' | 'pro' | 'enterprise'
  dailyQueryCount: number
  dailyResearchCount: number
}

interface UserStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  accessToken: string | null
  
  // Actions
  login: (user: User, token: string) => void
  setUser: (user: User | null) => void
  setAuthenticated: (auth: boolean) => void
  setLoading: (loading: boolean) => void
  setAccessToken: (token: string | null) => void
  logout: () => void
  incrementQueryCount: () => void
  incrementResearchCount: () => void
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  accessToken: null,
login: (user, token) => set({ 
    user, 
    accessToken: token,
    isAuthenticated: true,
    isLoading: false,
  }),
  
  
  setUser: (user) => set({ 
    user, 
    isAuthenticated: !!user,
    isLoading: false,
  }),
  
  setAuthenticated: (auth) => set({ isAuthenticated: auth }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setAccessToken: (token) => set({ accessToken: token }),
  
  logout: () => set({ 
    user: null, 
    isAuthenticated: false, 
    accessToken: null 
  }),
  
  incrementQueryCount: () => set((state) => ({
    user: state.user ? {
      ...state.user,
      dailyQueryCount: state.user.dailyQueryCount + 1,
    } : null,
  })),
  
  incrementResearchCount: () => set((state) => ({
    user: state.user ? {
      ...state.user,
      dailyResearchCount: state.user.dailyResearchCount + 1,
    } : null,
  })),
}))
