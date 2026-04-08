import { create } from 'zustand'

export type EntityType = 'PERSON' | 'ORG' | 'GPE' | 'EVENT' | 'ASSET' | 'INDICATOR' | 'TOPIC' | 'PRODUCT'
export type RelationType = 'ALLIED_WITH' | 'TRADES_WITH' | 'LEADS' | 'SANCTIONS' | 'OPPOSES' | 'COOPERATES_WITH' | 'INVESTS_IN' | 'MEMBER_OF' | 'OWNS' | 'BASED_IN' | 'SERVES' | 'PARTNER_OF'

export interface GraphNode {
  id: string
  name: string
  type: EntityType | string
  domain: string
  importance: number
  x?: number
  y?: number
  vx?: number
  vy?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: RelationType | string
  confidence: number
  strength: number
}

interface GraphStore {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNode: GraphNode | null
  hoveredNode: GraphNode | null
  layout: 'force' | 'hierarchical' | 'circular'
  viewMode: '2d' | '3d'
  isLoading: boolean

  // Actions
  setNodes: (nodes: GraphNode[]) => void
  setEdges: (edges: GraphEdge[]) => void
  addNodes: (nodes: GraphNode[]) => void
  addEdges: (edges: GraphEdge[]) => void
  selectNode: (node: GraphNode | null) => void
  hoverNode: (node: GraphNode | null) => void
  setLayout: (layout: 'force' | 'hierarchical' | 'circular') => void
  setViewMode: (mode: '2d' | '3d') => void
  setLoading: (loading: boolean) => void
  clearGraph: () => void
}

export const useGraphStore = create<GraphStore>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  hoveredNode: null,
  layout: 'force',
  viewMode: '2d',
  isLoading: false,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNodes: (newNodes) => set((state) => ({
    nodes: [...state.nodes, ...newNodes],
  })),

  addEdges: (newEdges) => set((state) => ({
    edges: [...state.edges, ...newEdges],
  })),

  selectNode: (node) => set({ selectedNode: node }),
  hoverNode: (node) => set({ hoveredNode: node }),

  setLayout: (layout) => set({ layout }),
  setViewMode: (mode) => set({ viewMode: mode }),

  setLoading: (loading) => set({ isLoading: loading }),

  clearGraph: () => set({ nodes: [], edges: [], selectedNode: null }),
}))
