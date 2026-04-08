import { useNavigate, useLocation } from 'react-router-dom'
import {
  Settings,
  Newspaper,
  TrendingUp,
  PieChart,
  MapPin,
  Network,
  Zap,
  Menu,
  X,
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { cn } from '@/utils/cn'
import * as React from 'react'

// Navigation items — Wireframe order: News → Finance → [Ontology] → Economy → Globe
const NAV_ITEMS = [
  { key: 'news', label: 'News', path: '/f2', icon: Newspaper },
  { key: 'finance', label: 'Finance', path: '/finance', icon: TrendingUp },
  { key: 'economy', label: 'Economy', path: '/f10', icon: PieChart },
  { key: 'globe', label: 'Globe', path: '/globe', icon: MapPin },
]

const ONTOLOGY_ITEM = {
  key: 'ontology',
  label: 'ONTOLOGY',
  path: 'http://localhost:3000',
  icon: Network
}

export default function TopBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <>
      {/* Dark Glassmorphism Header */}
      <header
        className={cn(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
          scrolled
            ? 'shadow-xl shadow-black/20'
            : ''
        )}
        style={{
          backgroundColor: scrolled ? 'rgba(10,11,15,0.95)' : 'rgba(10,11,15,0.90)',
          backdropFilter: 'blur(20px) saturate(200%)',
          WebkitBackdropFilter: 'blur(20px) saturate(200%)',
          borderBottom: scrolled ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(255,255,255,0.03)',
        }}
      >
        <div className="h-16 px-4 lg:px-12 flex items-center justify-between max-w-[1920px] mx-auto">

          {/* Left: Logo */}
          <div
            className="flex items-center gap-3 cursor-pointer group shrink-0"
            onClick={() => navigate('/f2')}
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,212,255,0.05))',
                border: '2px solid rgba(0,212,255,0.3)',
              }}
            >
              <span className="text-lg font-bold text-[#00D4FF]">A</span>
            </div>
            <div className="hidden md:flex flex-col">
              <span className="text-sm font-bold tracking-wider text-white" style={{ fontFamily: 'Georgia, serif' }}>
                AARAMBH
              </span>
              <span className="text-[10px] tracking-widest uppercase text-[#5A6278]">
                Intelligence Terminal
              </span>
            </div>
          </div>

          {/* Center: Main Nav + Ontology */}
          <nav className="hidden xl:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <NavButton
                key={item.key}
                item={item}
                isActive={isActive(item.path)}
                onClick={() => navigate(item.path)}
              />
            ))}

            {/* Divider */}
            <div className="w-px h-6 mx-3" style={{ background: 'rgba(255,255,255,0.08)' }} />

            {/* ONTOLOGY - Purple accent pill */}
            <OntologyButton
              item={ONTOLOGY_ITEM}
              isActive={isActive(ONTOLOGY_ITEM.path)}
              onClick={() => {
                if (ONTOLOGY_ITEM.path.startsWith('http')) {
                  window.open(ONTOLOGY_ITEM.path, '_blank');
                } else {
                  navigate(ONTOLOGY_ITEM.path);
                }
              }}
            />
          </nav>

          {/* Right: AI Query + Settings */}
          <div className="hidden xl:flex items-center gap-2">
            <button
              onClick={() => navigate('/query')}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-300',
                isActive('/query')
                  ? 'text-white bg-red-600 border-red-600'
                  : 'text-[#8B92A8] hover:text-white hover:bg-[rgba(255,255,255,0.06)]'
              )}
              style={{
                border: `1.5px solid ${isActive('/query') ? '#DC2626' : 'rgba(255,255,255,0.1)'}`,
              }}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>AI Query</span>
            </button>

            <button
              onClick={() => navigate('/settings')}
              className={cn(
                'w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-300',
                isActive('/settings')
                  ? 'text-white bg-[#00D4FF]'
                  : 'text-[#8B92A8] hover:text-white hover:bg-[rgba(255,255,255,0.06)]'
              )}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="xl:hidden w-9 h-9 rounded-lg flex items-center justify-center text-[#8B92A8] border border-[rgba(255,255,255,0.1)]"
          >
            {isMobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu - Dark Slide-down */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 top-16 z-40 xl:hidden"
          style={{
            background: 'linear-gradient(180deg, rgba(10,11,15,0.98) 0%, rgba(15,20,25,0.98) 100%)',
            backdropFilter: 'blur(20px)',
          }}
        >
          <div className="p-6 max-w-md mx-auto h-full overflow-y-auto">
            <div className="space-y-2 mb-6">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.key}
                  onClick={() => { navigate(item.path); setIsMobileMenuOpen(false) }}
                  className={cn(
                    'w-full flex items-center gap-4 p-4 rounded-xl transition-all duration-300',
                    isActive(item.path)
                      ? 'bg-[#00D4FF] text-[#0A0B0F]'
                      : 'bg-[#0F1419] text-[#8B92A8] border border-[rgba(255,255,255,0.06)]'
                  )}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  <span className="font-medium">{item.label}</span>
                </button>
              ))}
            </div>

            <button
              onClick={() => {
                if (ONTOLOGY_ITEM.path.startsWith('http')) {
                  window.open(ONTOLOGY_ITEM.path, '_blank');
                } else {
                  navigate(ONTOLOGY_ITEM.path);
                }
                setIsMobileMenuOpen(false);
              }}
              className={cn(
                'w-full flex items-center justify-center gap-3 p-5 rounded-xl mb-4 transition-all duration-300',
                isActive(ONTOLOGY_ITEM.path) ? 'text-white bg-[#8B5CF6]' : 'text-[#8B5CF6] bg-[#0F1419]'
              )}
              style={{
                border: '2px solid #8B5CF6',
                boxShadow: '0 4px 12px rgba(139,92,246,0.2)',
              }}
            >
              <ONTOLOGY_ITEM.icon className="w-5 h-5" />
              <span className="font-bold tracking-widest text-sm">{ONTOLOGY_ITEM.label}</span>
            </button>
          </div>
        </div>
      )}

      <div className="h-16" />
    </>
  )
}

// Regular Nav Button - Dark Theme
function NavButton({
  item,
  isActive,
  onClick
}: {
  item: { key: string; label: string; path: string; icon: React.ComponentType<{ className?: string }> }
  isActive: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-300',
        isActive
          ? 'bg-[#00D4FF] text-[#0A0B0F]'
          : 'text-[#8B92A8] hover:text-white hover:bg-[rgba(255,255,255,0.06)]'
      )}
      style={{
        transform: isActive ? 'translateY(-1px)' : 'none',
        boxShadow: isActive ? '0 4px 12px rgba(0,212,255,0.3)' : 'none',
      }}
    >
      <item.icon className="w-3.5 h-3.5" />
      <span>{item.label}</span>
    </button>
  )
}

// Ontology Button - Purple Accent Pill
function OntologyButton({
  item,
  isActive,
  onClick
}: {
  item: { key: string; label: string; path: string; icon: React.ComponentType<{ className?: string }> }
  isActive: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold tracking-wider text-xs transition-all duration-300',
      )}
      style={{
        backgroundColor: isActive ? '#8B5CF6' : 'rgba(139,92,246,0.1)',
        border: '2px solid #8B5CF6',
        boxShadow: isActive
          ? '0 4px 16px rgba(139,92,246,0.4), inset 0 2px 4px rgba(0,0,0,0.1)'
          : '0 2px 8px rgba(139,92,246,0.15)',
        transform: isActive ? 'scale(0.96)' : 'scale(1)',
        color: isActive ? 'white' : '#8B5CF6',
      }}
    >
      <item.icon className="w-4 h-4" />
      <span>{item.label}</span>
      <div
        className="w-2 h-2 rounded-full ml-1 transition-all duration-300"
        style={{
          backgroundColor: isActive ? 'white' : '#8B5CF6',
          boxShadow: isActive ? '0 0 8px white' : 'none',
        }}
      />
    </button>
  )
}
