import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTerminalStore } from '@/store/terminal.store'

const MODULE_SHORTCUTS: Record<string, string> = {
  'Alt+1': '/',
  'Alt+2': '/globe',
  'Alt+3': '/research',
  'Alt+4': '/graph',
  'Alt+5': '/query',
  'Alt+6': '/deep-research',
  'Alt+7': '/signals',
  'Alt+8': '/news',
  'Alt+9': '/analytics',
  'Alt+0': '/economy',
}

export const useKeyboardNav = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { 
    openCommandPalette, 
    closeCommandPalette, 
    focusCommandBar,
    commandPaletteOpen,
    setActiveModule,
  } = useTerminalStore()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Alt+1 to Alt+0 for module navigation
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const key = e.key
        if (/^[0-9]$/.test(key)) {
          const combo = `Alt+${key}`
          const path = MODULE_SHORTCUTS[combo]
          if (path) {
            e.preventDefault()
            navigate(path)
            setActiveModule(path)
          }
        }
      }

      // Ctrl+K = global search / command palette
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        if (commandPaletteOpen) {
          closeCommandPalette()
        } else {
          openCommandPalette()
        }
      }

      // Backtick = focus command bar
      if (e.key === '`' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Only focus if not already in an input
        const activeEl = document.activeElement
        if (activeEl?.tagName !== 'INPUT' && activeEl?.tagName !== 'TEXTAREA') {
          e.preventDefault()
          focusCommandBar()
        }
      }

      // Escape = close any overlay
      if (e.key === 'Escape') {
        closeCommandPalette()
      }
    }

    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [navigate, openCommandPalette, closeCommandPalette, focusCommandBar, commandPaletteOpen, setActiveModule])

  // Update active module on location change
  useEffect(() => {
    setActiveModule(location.pathname)
  }, [location.pathname, setActiveModule])
}
