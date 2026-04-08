import { ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface KPICardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: ReactNode
  className?: string
}

export default function KPICard({ 
  label, 
  value, 
  unit, 
  trend, 
  trendValue, 
  icon,
  className 
}: KPICardProps) {
  const trendColors = {
    up: 'text-online',
    down: 'text-error',
    neutral: 'text-text-muted',
  }

  const trendSymbols = {
    up: '↑',
    down: '↓',
    neutral: '→',
  }

  return (
    <div className={cn('kpi-card', className)}>
      {/* Label */}
      <div className="kpi-card__label">
        {label}
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-1">
        <span className="kpi-card__value">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && (
          <span className="text-text-muted text-sm font-data">
            {unit}
          </span>
        )}
      </div>

      {/* Trend */}
      {trend && trendValue && (
        <div className={cn('flex items-center gap-1 text-xs font-data', trendColors[trend])}>
          <span>{trendSymbols[trend]}</span>
          <span>{trendValue}</span>
        </div>
      )}

      {/* Icon */}
      {icon && (
        <div className="absolute top-3 right-3 text-text-muted opacity-50">
          {icon}
        </div>
      )}
    </div>
  )
}
