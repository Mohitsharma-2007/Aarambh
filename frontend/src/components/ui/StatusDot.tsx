import { cn } from '@/utils/cn'

interface StatusDotProps {
  status: 'online' | 'warning' | 'error' | 'idle'
  size?: 'sm' | 'md' | 'lg'
  pulse?: boolean
  label?: string
}

const statusColors = {
  online: 'bg-online',
  warning: 'bg-warning',
  error: 'bg-error',
  idle: 'bg-idle',
}

const sizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-3 h-3',
}

export default function StatusDot({ 
  status, 
  size = 'md', 
  pulse = true,
  label 
}: StatusDotProps) {
  return (
    <div className="flex items-center gap-1.5">
      <div
        className={cn(
          'rounded-full flex-shrink-0',
          statusColors[status],
          sizeClasses[size],
          pulse && status === 'online' && 'animate-pulse'
        )}
      />
      {label && (
        <span className="text-xs text-text-muted font-data">{label}</span>
      )}
    </div>
  )
}
