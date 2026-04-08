import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from 'sonner'
import TerminalShell from './layouts/TerminalShell'
import { useKeyboardNav } from './hooks/useKeyboardNav'
import { useTerminalStore } from './store/terminal.store'

import { useAIStore } from './store/ai.store'

function App() {
  const theme = useTerminalStore((state) => state.theme)
  const fetchProviders = useAIStore((state) => state.fetchProviders)
  const initialized = useAIStore((state) => state.initialized)

  useEffect(() => {
    if (!initialized) {
      fetchProviders()
    }
  }, [initialized, fetchProviders])

  // Initialize keyboard navigation
  useKeyboardNav()

  // Apply theme class to html element
  useEffect(() => {
    const html = document.documentElement
    html.classList.remove('light', 'dark')
    html.classList.add(theme)
  }, [theme])

  return (
    <TerminalShell>
      <Outlet />
      <Toaster
        position="top-right"
        theme={theme}
        toastOptions={{
          style: {
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-ui)',
          },
        }}
      />
    </TerminalShell>
  )
}

export default App
