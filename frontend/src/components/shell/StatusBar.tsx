import { useFeedStore } from '@/store/feed.store'
import { useGraphStore } from '@/store/graph.store'

export default function StatusBar() {
  const { events, isConnected, totalEvents } = useFeedStore()
  const { nodes, edges } = useGraphStore()

  const now = new Date()
  const timeStr = now.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
  const dateStr = now.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'short',
  })

  return (
    <footer className="status-bar">
      {/* Left section */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-2">
          <div className={`status-dot ${isConnected ? 'status-dot--online' : 'status-dot--idle'}`} />
          <span>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
        </div>

        <span className="text-border-default">│</span>

        {/* Feed stats */}
        <span>FEED: {events.length.toLocaleString()}</span>
        <span>TOTAL: {totalEvents.toLocaleString()}</span>

        <span className="text-border-default">│</span>

        {/* Graph stats */}
        <span>NODES: {nodes.length.toLocaleString()}</span>
        <span>EDGES: {edges.length.toLocaleString()}</span>
      </div>

      {/* Center section - API latency */}
      <div className="flex items-center gap-2">
        <span className="text-online">●</span>
        <span>API: 42ms</span>
        <span className="text-border-default">│</span>
        <span>Neo4j: 18ms</span>
        <span className="text-border-default">│</span>
        <span>Redis: 2ms</span>
      </div>

      {/* Right section - time */}
      <div className="flex items-center gap-2">
        <span>IST</span>
        <span className="text-border-default">│</span>
        <span>{dateStr}</span>
        <span>{timeStr}</span>
      </div>
    </footer>
  )
}
