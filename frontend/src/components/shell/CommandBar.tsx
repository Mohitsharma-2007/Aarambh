import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useTerminalStore } from '@/store/terminal.store'
import { parseCommand, getCommandAction } from '@/constants/commands'
import { toast } from 'sonner'

export default function CommandBar() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [input, setInput] = useState('')
  const { commandBarFocused, blurCommandBar, focusCommandBar } = useTerminalStore()

  // Focus input when command bar is focused
  useEffect(() => {
    if (commandBarFocused && inputRef.current) {
      inputRef.current.focus()
    }
  }, [commandBarFocused])

  // Handle blur
  const handleBlur = () => {
    blurCommandBar()
  }

  // Handle command submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedInput = input.trim()
    if (!trimmedInput) return

    // Check if it starts with >
    const commandStr = trimmedInput.startsWith('>')
      ? trimmedInput.slice(1).trim()
      : trimmedInput

    const { command, args } = parseCommand(commandStr)

    if (command) {
      const action = getCommandAction(command, args)

      if (action === 'help') {
        toast.info('Available commands', {
          description: 'SEARCH, ENTITY, GRAPH, RESEARCH, QUERY, ALERT, NEWS, SIGNALS, COMPARE, TIMELINE, HELP, CLEAR',
        })
      } else if (action === 'clear') {
        setInput('')
        toast.success('View cleared')
      } else {
        navigate(action)
      }
    } else {
      // Treat as search query
      navigate(`/research?q=${encodeURIComponent(commandStr)}`)
    }

    setInput('')
  }

  // Handle key events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      inputRef.current?.blur()
      blurCommandBar()
    }
  }

  return (
    <div className="command-bar">
      <div className="cmd-prompt">
        <ArrowRight className="cmd-arrow" />
        <span className="cmd-label">CMD</span>
      </div>
      <form onSubmit={handleSubmit} className="flex-1">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          onFocus={() => focusCommandBar()}
          placeholder="SEARCH entity | GRAPH query | RESEARCH topic..."
          className="cmd-input"
          autoComplete="off"
          spellCheck={false}
        />
      </form>
      <div className="text-xs text-text-muted font-data opacity-50">
        Press Enter to execute
      </div>
    </div>
  )
}
