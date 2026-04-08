import { Moon, Sun } from 'lucide-react'
import { useTerminalStore } from '@/store/terminal.store'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTerminalStore()

  return (
    <button
      onClick={toggleTheme}
      className="w-6 h-6 rounded flex items-center justify-center hover:bg-bg-hover transition-colors text-text-muted"
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? (
        <Sun className="w-3.5 h-3.5" />
      ) : (
        <Moon className="w-3.5 h-3.5" />
      )}
    </button>
  )
}
