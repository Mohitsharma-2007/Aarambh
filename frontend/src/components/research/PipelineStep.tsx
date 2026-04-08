import { Check, Loader2 } from 'lucide-react'
import { cn } from '@/utils/cn'

interface PipelineStepProps {
  step: string
  status: 'pending' | 'running' | 'completed' | 'error'
  index: number
}

export default function PipelineStep({ step, status, index }: PipelineStepProps) {
  return (
    <div className="flex items-center gap-3 py-2">
      {/* Status indicator */}
      <div
        className={cn(
          'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-data',
          status === 'completed' && 'bg-online text-bg-primary',
          status === 'running' && 'bg-warning text-bg-primary',
          status === 'error' && 'bg-error text-bg-primary',
          status === 'pending' && 'bg-bg-tertiary text-text-muted border border-border-subtle'
        )}
      >
        {status === 'completed' && <Check className="w-3 h-3" />}
        {status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
        {status === 'pending' && index + 1}
        {status === 'error' && '!'}
      </div>

      {/* Step name */}
      <div className="flex-1">
        <div
          className={cn(
            'text-sm',
            status === 'completed' && 'text-text-primary',
            status === 'running' && 'text-accent',
            status === 'error' && 'text-error',
            status === 'pending' && 'text-text-muted'
          )}
        >
          {step}
        </div>
      </div>

      {/* Status text */}
      <div className="text-xs font-data text-text-muted">
        {status === 'completed' && 'Done'}
        {status === 'running' && 'Running...'}
        {status === 'error' && 'Failed'}
      </div>
    </div>
  )
}
