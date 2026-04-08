import { Clock } from 'lucide-react'
import DomainBadge from '@/components/ui/DomainBadge'

interface TimelineEvent {
  id: string
  timestamp: string
  title: string
  description?: string
  domain: string
  importance: number
}

interface EntityTimelineProps {
  events: TimelineEvent[]
}

export default function EntityTimeline({ events }: EntityTimelineProps) {
  return (
    <div className="entity-timeline">
      {events.map((event, index) => (
        <div key={event.id} className="timeline-item">
          {/* Line */}
          <div className="timeline-line">
            <div className="timeline-dot" />
            {index < events.length - 1 && <div className="timeline-connector" />}
          </div>

          {/* Content */}
          <div className="timeline-content">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-3 h-3 text-text-muted" />
              <span className="text-xs font-data text-text-muted">
                {event.timestamp}
              </span>
              <DomainBadge domain={event.domain} />
            </div>
            <div className="text-sm text-text-primary">
              {event.title}
            </div>
            {event.description && (
              <div className="text-xs text-text-muted mt-1">
                {event.description}
              </div>
            )}
          </div>
        </div>
      ))}

      <style>{`
        .entity-timeline {
          display: flex;
          flex-direction: column;
        }
        .timeline-item {
          display: flex;
          gap: 12px;
        }
        .timeline-line {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex-shrink: 0;
        }
        .timeline-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--accent);
          border: 2px solid var(--bg-secondary);
        }
        .timeline-connector {
          width: 2px;
          flex: 1;
          background: var(--border-subtle);
          margin: 4px 0;
        }
        .timeline-content {
          flex: 1;
          padding-bottom: 16px;
        }
      `}</style>
    </div>
  )
}
