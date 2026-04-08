import { cn } from '@/utils/cn'

interface ProgressProps {
  value: number
  max?: number
  className?: string
  showLabel?: boolean
  variant?: 'default' | 'success' | 'warning' | 'error'
}

export function Progress({ 
  value, 
  max = 100, 
  className, 
  showLabel = false,
  variant = 'default' 
}: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  const variantColors = {
    default: 'bg-accent',
    success: 'bg-online',
    warning: 'bg-warning',
    error: 'bg-error',
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', variantColors[variant])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="mt-1 text-xs text-text-muted text-right">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  )
}

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  const variantStyles = {
    default: 'bg-bg-tertiary text-text-secondary',
    success: 'bg-online/20 text-online',
    warning: 'bg-warning/20 text-warning',
    error: 'bg-error/20 text-error',
    info: 'bg-accent/20 text-accent',
  }

  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 text-xs font-data rounded',
      variantStyles[variant],
      className
    )}>
      {children}
    </span>
  )
}

interface SkeletonProps {
  className?: string
  count?: number
}

export function Skeleton({ className, count = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'animate-pulse bg-bg-tertiary rounded',
            className
          )}
        />
      ))}
    </>
  )
}

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && (
        <div className="mb-4 text-text-muted opacity-50">
          {icon}
        </div>
      )}
      <h3 className="text-sm font-medium text-text-primary">{title}</h3>
      {description && (
        <p className="mt-1 text-xs text-text-muted">{description}</p>
      )}
      {action && (
        <div className="mt-4">{action}</div>
      )}
    </div>
  )
}
