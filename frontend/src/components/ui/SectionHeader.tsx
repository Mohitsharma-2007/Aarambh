import { cn } from '@/utils/cn'

interface SectionHeaderProps {
  title: string
  action?: React.ReactNode
  className?: string
}

export default function SectionHeader({ title, action, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex items-center gap-2 mb-3', className)}>
      <span className="text-xs font-data font-semibold text-text-muted tracking-wider">
        {title}
      </span>
      <div className="flex-1 h-px bg-border-subtle" />
      {action}
    </div>
  )
}
