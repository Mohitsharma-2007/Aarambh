import { useNavigate, useLocation } from 'react-router-dom'
import { Search, Settings, MoreHorizontal, Bell, Activity, TrendingUp, Globe, Zap } from 'lucide-react'
import { useTerminalStore } from '@/store/terminal.store'
import { MODULES } from '@/constants/modules'
import { cn } from '@/utils/cn'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/DropdownMenu'
import { useState, useEffect } from 'react'

// Module icons mapping
const MODULE_ICONS: Record<string, React.ReactNode> = {
  '1': <Activity className="w-4 h-4" />,
  '2': <Zap className="w-4 h-4" />,
  '3': <Globe className="w-4 h-4" />,
  '4': <TrendingUp className="w-4 h-4" />,
  '5': <Globe className="w-4 h-4" />,
  '6': <TrendingUp className="w-4 h-4" />,
  '7': <Zap className="w-4 h-4" />,
  '8': <Activity className="w-4 h-4" />,
  '9': <Zap className="w-4 h-4" />,
  '0': <TrendingUp className="w-4 h-4" />,
}

export default function TopBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { openCommandPalette, toggleTheme, theme } = useTerminalStore()
  const [isHovered, setIsHovered] = useState<string | null>(null)

  // Split modules into main (F1-F10) and secondary (others)
  const mainModules = MODULES.filter(m =>
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].includes(m.key)
  )
  const secondaryModules = MODULES.filter(m =>
    !['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].includes(m.key)
  )

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="topbar h-14 bg-[#0d0d1a] border-b border-[#1e1e32] px-4 flex items-center gap-6">
      {/* Logo */}
      <div 
        className="flex items-center gap-3 cursor-pointer group"
        onClick={() => navigate('/')}
      >
        <div className="relative">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#3B82F6]/20 group-hover:shadow-[#3B82F6]/40 transition-shadow">
            <span className="text-white font-bold text-lg">A</span>
          </div>
          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-[#10B981] rounded-full border-2 border-[#0d0d1a]"></div>
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-sm tracking-wider text-white">
            AARAMBH
          </span>
          <span className="text-[10px] text-[#666] tracking-widest uppercase">
            Intelligence Terminal
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="h-8 w-px bg-gradient-to-b from-transparent via-[#2d2d44] to-transparent"></div>

      {/* Market Status Indicator */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-[#12121f] rounded-lg border border-[#1e1e32]">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></div>
          <span className="text-xs text-[#10B981] font-medium">LIVE</span>
        </div>
        <div className="w-px h-4 bg-[#2d2d44]"></div>
        <span className="text-xs text-[#888]">NSE</span>
      </div>

      {/* Module tabs */}
      <nav className="flex-1 flex items-center gap-1">
        {mainModules.map((module) => (
          <button
            key={module.key}
            onClick={() => navigate(module.path)}
            className={cn(
              'relative flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200',
              isActive(module.path)
                ? 'bg-[#1e1e32] text-white shadow-lg shadow-black/20'
                : 'text-[#888] hover:text-white hover:bg-[#1a1a2e]'
            )}
            title={module.description}
          >
            {/* Active indicator */}
            {isActive(module.path) && (
              <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-[#3B82F6]/10 to-transparent border border-[#3B82F6]/30"></div>
            )}
            <span className={cn(
              'transition-colors',
              isActive(module.path) ? 'text-[#3B82F6]' : ''
            )}>
              {MODULE_ICONS[module.key] || <Activity className="w-4 h-4" />}
            </span>
            <span className="relative z-10">{module.label}</span>
            <span className={cn(
              'relative z-10 px-1.5 py-0.5 rounded text-[10px] font-mono',
              isActive(module.path) 
                ? 'bg-[#3B82F6]/20 text-[#3B82F6]' 
                : 'bg-[#2d2d44] text-[#666]'
            )}>
              F{module.key}
            </span>
          </button>
        ))}

        {/* Dropdown for secondary modules */}
        {secondaryModules.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button 
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-[#888] hover:text-white hover:bg-[#1a1a2e] transition-all"
                onMouseEnter={() => setIsHovered('more')}
                onMouseLeave={() => setIsHovered(null)}
              >
                <MoreHorizontal className="w-4 h-4" />
                <span>More</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-[#12121f] border border-[#1e1e32] shadow-xl shadow-black/50 p-1">
              {secondaryModules.map((module) => (
                <DropdownMenuItem
                  key={module.key}
                  onClick={() => navigate(module.path)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors',
                    isActive(module.path) 
                      ? 'bg-[#1e1e32] text-white' 
                      : 'text-[#aaa] hover:bg-[#1a1a2e] hover:text-white'
                  )}
                >
                  <span className={cn(
                    'w-6 h-6 rounded flex items-center justify-center text-xs',
                    isActive(module.path) ? 'bg-[#3B82F6]/20 text-[#3B82F6]' : 'bg-[#2d2d44] text-[#666]'
                  )}>
                    {module.shortcut}
                  </span>
                  <span className="flex-1">{module.label}</span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </nav>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-lg bg-[#12121f] border border-[#1e1e32] flex items-center justify-center text-[#888] hover:text-white hover:border-[#2d2d44] transition-all">
          <Bell className="w-4 h-4" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#EF4444] rounded-full"></span>
        </button>

        {/* Global search */}
        <button
          onClick={() => openCommandPalette()}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#12121f] border border-[#1e1e32] hover:border-[#3B82F6] transition-all group"
        >
          <Search className="w-4 h-4 text-[#666] group-hover:text-[#3B82F6] transition-colors" />
          <span className="text-xs text-[#666] font-mono">Search...</span>
          <span className="text-[10px] text-[#444] bg-[#1a1a2e] px-1.5 py-0.5 rounded">Ctrl+K</span>
        </button>

        {/* Theme toggle */}
        <button
          onClick={() => toggleTheme()}
          className="w-9 h-9 rounded-lg bg-[#12121f] border border-[#1e1e32] flex items-center justify-center text-[#888] hover:text-white hover:border-[#2d2d44] transition-all"
          title="Toggle theme"
        >
          <div className={cn(
            'w-5 h-5 rounded-full transition-all',
            theme === 'dark' ? 'bg-[#1a1a2e]' : 'bg-[#F59E0B]'
          )}>
            <div className={cn(
              'w-full h-full rounded-full transition-transform',
              theme === 'dark' ? 'bg-[#666]' : 'bg-white'
            )} />
          </div>
        </button>

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className={cn(
            'w-9 h-9 rounded-lg border flex items-center justify-center transition-all',
            isActive('/settings')
              ? 'bg-[#3B82F6]/20 border-[#3B82F6] text-[#3B82F6]'
              : 'bg-[#12121f] border-[#1e1e32] text-[#888] hover:text-white hover:border-[#2d2d44]'
          )}
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
