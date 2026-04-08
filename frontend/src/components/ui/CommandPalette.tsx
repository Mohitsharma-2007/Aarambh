import { useState } from 'react'
import { Search, X } from 'lucide-react'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

const COMMANDS = [
  { id: 'overview', label: 'Overview', shortcut: 'Alt+1', path: '/' },
  { id: 'globe', label: 'Globe View', shortcut: 'Alt+2', path: '/globe' },
  { id: 'research', label: 'Research', shortcut: 'Alt+3', path: '/research' },
  { id: 'graph', label: 'Knowledge Graph', shortcut: 'Alt+4', path: '/graph' },
  { id: 'query', label: 'AI Query', shortcut: 'Alt+5', path: '/query' },
  { id: 'deep-research', label: 'Deep Research', shortcut: 'Alt+6', path: '/deep-research' },
  { id: 'signals', label: 'Signals', shortcut: 'Alt+7', path: '/signals' },
  { id: 'news', label: 'News Feed', shortcut: 'Alt+8', path: '/news' },
  { id: 'analytics', label: 'Analytics', shortcut: 'Alt+9', path: '/analytics' },
  { id: 'economy', label: 'Economy', shortcut: 'Alt+0', path: '/economy' },
]

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('')

  if (!isOpen) return null

  const filteredCommands = COMMANDS.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Palette */}
      <div className="relative w-full max-w-lg bg-bg-secondary border border-border-subtle rounded-lg shadow-2xl overflow-hidden">
        {/* Search */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border-subtle">
          <Search className="w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search commands..."
            className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
            autoFocus
          />
          <button
            onClick={onClose}
            className="p-1 hover:bg-bg-hover rounded text-text-muted hover:text-text-primary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Commands */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => {
                window.location.href = cmd.path
                onClose()
              }}
              className="w-full flex items-center justify-between px-3 py-2 rounded text-sm hover:bg-bg-hover transition-colors"
            >
              <span className="text-text-primary">{cmd.label}</span>
              <span className="text-xs text-text-muted font-data">{cmd.shortcut}</span>
            </button>
          ))}
          {filteredCommands.length === 0 && (
            <div className="px-3 py-8 text-center text-sm text-text-muted">
              No commands found
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-border-subtle bg-bg-tertiary text-xs text-text-muted">
          Press <kbd className="px-1.5 py-0.5 bg-bg-secondary rounded text-text-secondary">Esc</kbd> to close
        </div>
      </div>
    </div>
  )
}
