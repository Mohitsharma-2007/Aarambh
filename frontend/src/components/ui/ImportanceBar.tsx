import { cn } from '@/utils/cn'

interface ImportanceBarProps {
  value: number // 0-100
  max?: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function ImportanceBar({ 
  value, 
  max = 100, 
  showLabel = false,
  size = 'md'
}: ImportanceBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  
  const getColor = () => {
    if (percentage >= 80) return 'from-error to-warning'
    if (percentage >= 60) return 'from-warning to-eco'
    if (percentage >= 40) return 'from-eco to-tech'
    return 'from-tech to-cli'
  }

  const heightClass = {
    sm: 'h-1',
    md: 'h-1.5',
    lg: 'h-2',
  }[size]

  return (
    <div className="flex items-center gap-2">
      <div className={cn('flex-1 bg-bg-tertiary rounded-full overflow-hidden', heightClass)}>
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-300',
            getColor()
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs text-text-muted font-data w-8 text-right">
          {value}
        </span>
      )}
    </div>
  )
}
