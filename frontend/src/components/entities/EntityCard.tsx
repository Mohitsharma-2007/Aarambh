import { Globe, Building2, User } from 'lucide-react'
import { cn } from '@/utils/cn'
import DomainBadge from '@/components/ui/DomainBadge'

interface EntityCardProps {
  entity: {
    id: string
    name: string
    type: 'PERSON' | 'ORG' | 'GPE' | 'EVENT' | 'ASSET' | 'INDICATOR'
    domain: string
    importance: number
    description?: string
  }
  onClick?: () => void
  selected?: boolean
}

const TYPE_ICONS: Record<string, any> = {
  PERSON: User,
  ORG: Building2,
  GPE: Globe,
  EVENT: Globe,
  ASSET: Globe,
  INDICATOR: Globe,
}

export default function EntityCard({ entity, onClick, selected }: EntityCardProps) {
  const TypeIcon = TYPE_ICONS[entity.type] || Globe

  return (
    <div
      onClick={onClick}
      className={cn(
        'entity-card',
        selected && 'entity-card--selected'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded bg-accent/10 flex items-center justify-center flex-shrink-0">
          <TypeIcon className="w-4 h-4 text-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-text-primary truncate">
            {entity.name}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <DomainBadge domain={entity.domain} />
            <span className="text-xs text-text-muted font-data">
              {entity.type}
            </span>
          </div>
          {entity.description && (
            <div className="text-xs text-text-muted mt-2 line-clamp-2">
              {entity.description}
            </div>
          )}
        </div>
        <div className="text-xs font-data text-text-muted">
          {entity.importance}/10
        </div>
      </div>

      <style>{`
        .entity-card {
          padding: 12px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.1s ease;
        }
        .entity-card:hover {
          background: var(--bg-hover);
          border-color: var(--border-default);
        }
        .entity-card--selected {
          background: var(--bg-active);
          border-color: var(--accent);
        }
      `}</style>
    </div>
  )
}
