import { ReactNode } from 'react'
import { cn } from '@/utils/cn'

const DOMAIN_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  geopolitics: { color: '#4a9eed', bg: 'rgba(74,158,237,0.12)', label: 'GEOPOLITICS' },
  economics: { color: '#22c55e', bg: 'rgba(34,197,94,0.12)', label: 'ECONOMICS' },
  defense: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'DEFENSE' },
  technology: { color: '#06b6d4', bg: 'rgba(6,182,212,0.12)', label: 'TECHNOLOGY' },
  climate: { color: '#14b8a6', bg: 'rgba(20,184,166,0.12)', label: 'CLIMATE' },
  society: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'SOCIETY' },
  politics: { color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)', label: 'POLITICS' },
}

interface DomainBadgeProps {
  domain: string
  color?: string
  bg?: string
  children?: ReactNode
  className?: string
}

export default function DomainBadge({ 
  domain, 
  color,
  bg,
  children,
  className 
}: DomainBadgeProps) {
  const config = DOMAIN_CONFIG[domain.toLowerCase()] || { color: '#4a9eed', bg: 'rgba(74,158,237,0.12)', label: domain.toUpperCase() }
  const finalColor = color || config.color
  const finalBg = bg || config.bg

  return (
    <span 
      className={cn('domain-badge', className)}
      style={{ 
        backgroundColor: finalBg,
        color: finalColor,
        border: `1px solid ${finalColor}33`,
      }}
    >
      {config.label}
      {children}
    </span>
  )
}
