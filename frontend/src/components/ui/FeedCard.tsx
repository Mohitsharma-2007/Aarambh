import type { Domain } from '@/store/feed.store'
import { getDomainConfig } from '@/constants/domains'
import { cn } from '@/utils/cn'
import { formatDistanceToNow } from 'date-fns'
import { MessageSquare } from 'lucide-react'

interface FeedCardProps {
  event: {
    id: string
    title: string
    summary: string
    domain: Domain
    source: string
    sourceUrl: string
    publishedAt: string
    importance: number
    entities: string[]
    sentiment: number
    isNew?: boolean
  }
  onClick?: () => void
  onInsight?: (event: any) => void
}

export default function FeedCard({ event, onClick, onInsight }: FeedCardProps) {
  const domainConfig = getDomainConfig(event.domain)
  
  const timeAgo = formatDistanceToNow(new Date(event.publishedAt), { 
    addSuffix: true 
  })

  return (
    <div
      className={cn(
        'feed-card feed-card-enter relative',
        event.isNew && 'border-l-2 border-l-accent'
      )}
      style={{ '--domain-color': domainConfig.color } as React.CSSProperties}
      onClick={onClick}
    >
      {/* Insight button */}
      {onInsight && (
        <button
          className="absolute top-2 right-2 p-1 bg-bg-secondary/80 border border-border-subtle rounded text-xs flex items-center gap-1 text-accent hover:bg-accent/20 z-10"
          onClick={(e) => {
            e.stopPropagation()
            onInsight(event)
          }}
        >
          <MessageSquare className="w-3 h-3" />
          <span>Insight</span>
        </button>
      )}
      {/* Domain accent bar */}
      <div 
        className="feed-card__accent"
        style={{ backgroundColor: domainConfig.color }}
      />

      {/* Card body */}
      <div className="feed-card__body">
        {/* Title */}
        <h3 className="feed-card__title">
          {event.title}
        </h3>

        {/* Meta row */}
        <div className="feed-card__meta">
          {/* Domain badge */}
          <span 
            className="domain-badge"
            style={{ 
              backgroundColor: domainConfig.bg,
              color: domainConfig.color,
              border: `1px solid ${domainConfig.color}33`,
            }}
          >
            {domainConfig.label}
          </span>

          {/* Source */}
          <span className="feed-card__source">
            {event.source}
          </span>

          {/* Time */}
          <span className="feed-card__time">
            {timeAgo}
          </span>

          {/* Importance score */}
          {event.importance >= 7 && (
            <span className="text-warning text-xs font-data">
              ★{event.importance}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
