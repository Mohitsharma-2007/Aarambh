import { useState, useEffect } from 'react'
import { Search, Brain } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { MODULES } from '@/constants/modules'

export default function GlobalSearch() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  // Listen for Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(true)
      }
      if (e.key === 'Escape') {
        setOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleSelect = (path: string) => {
    navigate(path)
    setOpen(false)
    setQuery('')
  }

  const filteredModules = MODULES.filter(m => 
    m.label.toLowerCase().includes(query.toLowerCase())
  )

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-bg-primary/80 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />
      
      {/* Dialog */}
      <div className="relative w-full max-w-xl bg-bg-secondary border border-border-default rounded-lg shadow-2xl overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border-subtle">
          <Search className="w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search modules, entities, commands..."
            className="flex-1 bg-transparent text-text-primary text-sm outline-none"
            autoFocus
          />
          <kbd className="px-2 py-0.5 text-xs text-text-muted bg-bg-tertiary border border-border-subtle rounded">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {/* Quick Navigate */}
          <div className="px-2 py-1.5 text-xs text-text-muted font-data">QUICK NAVIGATE</div>
          {filteredModules.map((module) => (
            <button
              key={module.key}
              onClick={() => handleSelect(module.path)}
              className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-bg-hover transition-colors"
            >
              <span className="text-text-primary text-sm">{module.label}</span>
              <span className="ml-auto text-xs text-text-muted font-data">{module.key}</span>
            </button>
          ))}

          {/* Commands */}
          <div className="px-2 py-1.5 mt-2 text-xs text-text-muted font-data">COMMANDS</div>
          <button
            onClick={() => { navigate('/research'); setOpen(false) }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-bg-hover transition-colors"
          >
            <Search className="w-4 h-4 text-text-muted" />
            <span className="text-text-primary text-sm">Search entities...</span>
          </button>
          <button
            onClick={() => { navigate('/deep-research'); setOpen(false) }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-bg-hover transition-colors"
          >
            <Brain className="w-4 h-4 text-text-muted" />
            <span className="text-text-primary text-sm">Start deep research...</span>
          </button>
        </div>
      </div>
    </div>
  )
}
