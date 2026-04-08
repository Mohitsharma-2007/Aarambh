import { useGraphStore } from '@/store/graph.store'

const NODE_COLORS: Record<string, string> = {
  PERSON: '#4a9eed',
  ORG: '#8b5cf6',
  GPE: '#22c55e',
  EVENT: '#ef4444',
  ASSET: '#f59e0b',
  INDICATOR: '#06b6d4',
}

export default function GraphCanvas() {
  const { nodes, edges, selectedNode, selectNode } = useGraphStore()

  // Demo data if empty
  const graphData = {
    nodes: nodes.length > 0 ? nodes : [
      { id: '1', name: 'India', type: 'GPE', domain: 'geopolitics', importance: 10 },
      { id: '2', name: 'China', type: 'GPE', domain: 'geopolitics', importance: 9 },
      { id: '3', name: 'USA', type: 'GPE', domain: 'geopolitics', importance: 9 },
      { id: '4', name: 'Narendra Modi', type: 'PERSON', domain: 'politics', importance: 8 },
      { id: '5', name: 'BRICS', type: 'ORG', domain: 'economics', importance: 7 },
    ],
    links: edges.length > 0 ? edges.map(e => ({ ...e, source: e.source, target: e.target })) : [
      { id: 'l1', source: '1', target: '2', type: 'OPPOSES', confidence: 0.9, strength: 0.8 },
      { id: 'l2', source: '1', target: '3', type: 'COOPERATES_WITH', confidence: 0.7, strength: 0.6 },
      { id: 'l3', source: '1', target: '5', type: 'ALLIED_WITH', confidence: 0.95, strength: 0.9 },
      { id: 'l4', source: '4', target: '1', type: 'LEADS', confidence: 1, strength: 1 },
    ],
  }

  // Placeholder - in production would use react-force-graph-2d
  console.log('Graph data:', graphData, 'Selected:', selectedNode, 'Select fn:', selectNode, 'Colors:', NODE_COLORS)

  return (
    <div className="h-full w-full bg-bg-primary flex items-center justify-center">
      <div className="text-text-muted text-sm">Graph visualization requires react-force-graph-2d package</div>
    </div>
  )
}
