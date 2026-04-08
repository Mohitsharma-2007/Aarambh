import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface TerminalStore {
  activeModule: string
  theme: 'dark' | 'light'
  commandBarFocused: boolean
  commandPaletteOpen: boolean
  
  // Actions
  setActiveModule: (path: string) => void
  setTheme: (theme: 'dark' | 'light') => void
  toggleTheme: () => void
  focusCommandBar: () => void
  blurCommandBar: () => void
  openCommandPalette: () => void
  closeCommandPalette: () => void
}

export const useTerminalStore = create<TerminalStore>()(
  persist(
    (set) => ({
      activeModule: '/',
      theme: 'dark',
      commandBarFocused: false,
      commandPaletteOpen: false,

      setActiveModule: (path) => set({ activeModule: path }),
      setTheme: (theme) => set({ theme }),
      
      
      toggleTheme: () => set((state) => ({ 
        theme: state.theme === 'dark' ? 'light' : 'dark' 
      })),
      
      focusCommandBar: () => set({ commandBarFocused: true }),
      blurCommandBar: () => set({ commandBarFocused: false }),
      
      openCommandPalette: () => set({ commandPaletteOpen: true }),
      closeCommandPalette: () => set({ commandPaletteOpen: false }),
    }),
    {
      name: 'aarambh-terminal',
      partialize: (state) => ({ 
        theme: state.theme,
        activeModule: state.activeModule,
      }),
    }
  )
)
