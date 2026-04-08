import { Globe, Building2, User } from 'lucide-react'
import DomainBadge from '@/components/ui/DomainBadge'
import ImportanceBar from '@/components/ui/ImportanceBar'

interface EntityHeaderProps {
  entity: {
    id: string
    name: string
    type: 'PERSON' | 'ORG' | 'GPE' | 'EVENT' | 'ASSET' | 'INDICATOR'
    domain: string
    importance: number
    aliases?: string[]
  }
}

const TYPE_ICONS: Record<string, any> = {
  PERSON: User,
  ORG: Building2,
  GPE: Globe,
  EVENT: Globe,
  ASSET: Globe,
  INDICATOR: Globe,
}

export default function EntityHeader({ entity }: EntityHeaderProps) {
  const TypeIcon = TYPE_ICONS[entity.type] || Globe

  return (
    <div className="entity-header">
      {/* Icon */}
      <div className="w-14 h-14 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
        <TypeIcon className="w-7 h-7 text-accent" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h1 className="text-xl font-semibold text-text-primary">
          {entity.name}
        </h1>
        <div className="flex items-center gap-3 mt-2">
          <DomainBadge domain={entity.domain} />
          <span className="text-xs text-text-muted font-data">
            {entity.type}
          </span>
          <span className="text-xs text-text-muted">•</span>
          <span className="text-xs text-text-muted font-data">
            ID: {entity.id}
          </span>
        </div>
        {entity.aliases && entity.aliases.length > 0 && (
          <div className="text-xs text-text-muted mt-2">
            Also known as: {entity.aliases.slice(0, 3).join(', ')}
          </div>
        )}
      </div>

      {/* Importance */}
      <div className="flex flex-col items-end gap-1">
        <span className="text-xs text-text-muted font-data">IMPORTANCE</span>
        <div className="w-24">
          <ImportanceBar value={entity.importance} max={10} showLabel />
        </div>
      </div>

      <style>{`
        .entity-header {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          padding: 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: 8px;
        }
      `}</style>
    </div>
  )
}
