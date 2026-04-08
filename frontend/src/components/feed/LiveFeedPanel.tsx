import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import FeedCard from '@/components/ui/FeedCard'
import { useFeedStore } from '@/store/feed.store'

export default function LiveFeedPanel() {
  const { events } = useFeedStore()
  const parentRef = useRef<HTMLDivElement>(null)

  const rowVirtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 5,
  })

  return (
    <div
      ref={parentRef}
      className="h-full overflow-y-auto"
      style={{ contain: 'strict' }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const event = events[virtualRow.index]
          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <FeedCard
                event={event}
                onClick={() => console.log('Clicked:', event.id)}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
