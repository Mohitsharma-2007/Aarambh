import { cn } from '@/utils/cn'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  onClick?: () => void
}

export function Card({ children, className, hover = false, onClick }: CardProps) {
  return (
    <div
      className={cn(
        'bg-bg-secondary border border-border-subtle rounded-lg p-4',
        className,
        hover && 'hover:bg-bg-hover hover:border-border-focus cursor-pointer transition-colors',
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return (
    <div className={cn('mb-3', className)}>
      {children}
    </div>
  )
}

interface CardTitleProps {
  children: React.ReactNode
  className?: string
}

export function CardTitle({ children, className }: CardTitleProps) {
  return (
    <h3 className={cn('text-sm font-data font-semibold text-text-primary', className)}>
      {children}
    </h3>
  )
}

interface CardContentProps {
  children: React.ReactNode
  className?: string
}

export function CardContent({ children, className }: CardContentProps) {
  return (
    <div className={className}>
      {children}
    </div>
  )
}

interface CardFooterProps {
  children: React.ReactNode
  className?: string
}

export function CardFooter({ children, className }: CardFooterProps) {
  return (
    <div className={cn('mt-3 pt-3 border-t border-border-subtle', className)}>
      {children}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: React.ReactNode
}

export function StatCard({ label, value, change, trend = 'neutral', icon }: StatCardProps) {
  const trendColors = {
    up: 'text-online',
    down: 'text-error',
    neutral: 'text-text-muted',
  }

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-text-muted mb-1">{label}</p>
          <p className="text-2xl font-data font-semibold text-text-primary">{value}</p>
          {change && (
            <p className={cn('text-xs mt-1', trendColors[trend])}>{change}</p>
          )}
        </div>
        {icon && (
          <div className="p-2 bg-bg-tertiary rounded-lg text-accent">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}
