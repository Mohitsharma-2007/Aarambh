import { X, ExternalLink, Globe, Building2, User, Calendar, Shield } from 'lucide-react'
import { useGraphStore } from '@/store/graph.store'
import DomainBadge from '@/components/ui/DomainBadge'
import ImportanceBar from '@/components/ui/ImportanceBar'

const TYPE_ICONS: Record<string, any> = {
  PERSON: User,
  ORG: Building2,
  GPE: Globe,
  EVENT: Calendar,
  ASSET: Shield,
  INDICATOR: Shield,
}

export default function NodeDetailPanel() {
  const { selectedNode, selectNode } = useGraphStore()

  if (!selectedNode) return null

  const TypeIcon = TYPE_ICONS[selectedNode.type] || Globe

  return (
    <div className="absolute right-0 top-0 bottom-0 w-80 bg-bg-secondary border-l border-border-subtle z-20 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
        <span className="text-xs font-data text-text-muted">ENTITY DETAILS</span>
        <button
          onClick={() => selectNode(null)}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-bg-hover text-text-muted"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Entity header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center flex-shrink-0">
            <TypeIcon className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-text-primary truncate">
              {selectedNode.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <DomainBadge domain={selectedNode.domain} />
              <span className="text-xs text-text-muted font-data">
                {selectedNode.type}
              </span>
            </div>
          </div>
        </div>

        {/* Properties */}
        <div className="space-y-4">
          {/* Importance */}
          <div>
            <div className="text-xs text-text-muted mb-2 font-data">IMPORTANCE</div>
            <ImportanceBar value={selectedNode.importance} max={10} showLabel />
          </div>

          {/* ID */}
          <div>
            <div className="text-xs text-text-muted mb-1 font-data">ENTITY ID</div>
            <div className="text-sm font-data text-text-secondary">
              {selectedNode.id}
            </div>
          </div>

          {/* Domain */}
          <div>
            <div className="text-xs text-text-muted mb-1 font-data">DOMAIN</div>
            <div className="text-sm text-text-secondary">
              {selectedNode.domain}
            </div>
          </div>

          {/* Connections */}
          <div>
            <div className="text-xs text-text-muted mb-1 font-data">CONNECTIONS</div>
            <div className="text-sm font-data text-text-secondary">
              12 entities
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 pt-4 border-t border-border-subtle space-y-2">
          <button className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent/10 border border-accent/30 rounded text-accent text-sm hover:bg-accent/20 transition-colors">
            <ExternalLink className="w-4 h-4" />
            Open in Research
          </button>
          <button className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-bg-tertiary border border-border-subtle rounded text-text-secondary text-sm hover:bg-bg-hover transition-colors">
            <Globe className="w-4 h-4" />
            Expand Relations
          </button>
        </div>
      </div>
    </div>
  )
}
