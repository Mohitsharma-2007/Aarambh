import { ReactNode } from 'react'
import TopBar from '@/components/shell/TopBar'

interface TerminalShellProps {
  children: ReactNode
}

export default function TerminalShell({ children }: TerminalShellProps) {
  return (
    <div className="terminal-shell min-h-screen bg-[var(--bg-primary)]">
      {/* Top bar with module tabs */}
      <TopBar />

      {/* Main content area */}
      <main className="flex-1 overflow-auto scrollable">
        {children}
      </main>
    </div>
  )
}
