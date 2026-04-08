import PipelineStep from './PipelineStep'

interface PipelineProgressProps {
  steps: Array<{
    step: string
    status: 'pending' | 'running' | 'completed' | 'error'
  }>
}

export default function PipelineProgress({ steps }: PipelineProgressProps) {
  return (
    <div className="pipeline-progress">
      <div className="text-xs font-data text-text-muted mb-3">RESEARCH PIPELINE</div>
      <div className="space-y-1">
        {steps.map((s, i) => (
          <PipelineStep key={i} step={s.step} status={s.status} index={i} />
        ))}
      </div>

      <style>{`
        .pipeline-progress {
          padding: 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: 8px;
        }
      `}</style>
    </div>
  )
}
