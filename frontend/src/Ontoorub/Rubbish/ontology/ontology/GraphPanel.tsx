import React, { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import {
  RefreshCw, Maximize2, Share2, Info,
  Layers, Database, Zap, Activity, Filter, Eye, EyeOff,
  Plus, Minus, Target
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils/cn'

interface GraphNode {
  uuid: string
  name: string
  labels: string[]
  attributes?: Record<string, any>
  summary?: string
  created_at?: string
}

interface GraphEdge {
  uuid: string
  source_node_uuid: string
  target_node_uuid: string
  fact_type: string
  name: string
  fact?: string
  episodes?: string[]
  created_at?: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  node_count?: number
  edge_count?: number
}

interface GraphPanelProps {
  graphData: GraphData | null
  loading?: boolean
  currentPhase?: number
  isSimulating?: boolean
  onRefresh?: () => void
  onToggleMaximize?: () => void
}

interface SelectedItem {
  type: 'node' | 'edge'
  data: any
  entityType?: string
  color?: string
}

const COLORS = [
  '#6366f1', // Indigo
  '#f43f5e', // Rose
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#3b82f6', // Blue
  '#8b5cf6', // Violet
  '#06b6d4', // Cyan
  '#ec4899', // Pink
  '#f97316', // Orange
  '#84cc16'  // Lime
]

export const GraphPanel: React.FC<GraphPanelProps> = ({
  graphData,
  loading = false,
  currentPhase = -1,
  isSimulating = false,
  onRefresh,
  onToggleMaximize,
}) => {
  const graphContainerRef = useRef<HTMLDivElement>(null)
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null)
  const [showEdgeLabels, setShowEdgeLabels] = useState(true)
  const [showFinishedHint, setShowFinishedHint] = useState(false)
  const [wasSimulating, setWasSimulating] = useState(false)
  const simulationRef = useRef<any>(null)
  const zoomRef = useRef<any>(null)
  const svgRef = useRef<any>(null)
  const gRef = useRef<any>(null)

  useEffect(() => {
    if (wasSimulating && !isSimulating) setShowFinishedHint(true)
    setWasSimulating(isSimulating)
  }, [isSimulating, wasSimulating])

  const entityTypes = React.useMemo(() => {
    if (!graphData?.nodes) return []
    const typeMap: Record<string, { name: string; count: number; color: string }> = {}
    
    // Use for loop instead of forEach for better performance with large datasets
    for (let i = 0; i < graphData.nodes.length; i++) {
      const node = graphData.nodes[i]
      const type = node.labels?.[0] || 'Entity'
      if (!typeMap[type]) {
        typeMap[type] = { name: type, count: 0, color: COLORS[Object.keys(typeMap).length % COLORS.length] }
      }
      typeMap[type].count++
    }
    return Object.values(typeMap)
  }, [graphData])

  const getColor = useCallback((type: string) => {
    const found = entityTypes.find(t => t.name === type)
    return found?.color || '#6366f1'
  }, [entityTypes])

  useEffect(() => {
    if (!graphContainerRef.current || !graphData) return
    if (simulationRef.current) simulationRef.current.stop()

    const container = graphContainerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    d3.select(container).selectAll('svg').remove()

    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('cursor', 'grab')

    // Add a rect as a background to capture zoom events in empty areas
    svg.append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', 'transparent')
      .on('click', () => setSelectedItem(null))

    const nodesData = graphData.nodes || []
    const edgesData = graphData.edges || []
    if (nodesData.length === 0) return

    const nodeMap: Record<string, GraphNode> = {}
    nodesData.forEach(n => nodeMap[n.uuid] = n)

    const nodes = nodesData.map(n => ({
      id: n.uuid,
      name: n.name || 'Unnamed',
      type: n.labels?.find(l => l !== 'Entity') || 'Entity',
      rawData: n,
      x: width / 2 + (Math.random() - 0.5) * 100,
      y: height / 2 + (Math.random() - 0.5) * 100,
    }))

    const nodeIds = new Set(nodes.map(n => n.id))
    const edges = edgesData
      .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
      .map(e => ({
        source: e.source_node_uuid,
        target: e.target_node_uuid,
        type: e.fact_type || e.name || 'RELATED',
        name: e.name || e.fact_type || 'RELATED',
        rawData: {
          ...e,
          source_name: nodeMap[e.source_node_uuid]?.name,
          target_name: nodeMap[e.target_node_uuid]?.name,
        }
      }))

    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges as any).id((d: any) => d.id).distance(180))
      .force('charge', d3.forceManyBody().strength(-800))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(60))

    simulationRef.current = simulation
    const g = svg.append('g')

    gRef.current = g
    const zoom = d3.zoom().extent([[0, 0], [width, height]]).scaleExtent([0.1, 4]).on('zoom', (event) => {
      g.attr('transform', event.transform)
    })
    zoomRef.current = zoom
    svgRef.current = svg
    svg.call(zoom as any)

    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('stroke', 'rgba(255,255,255,0.08)')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event: any, d: any) => {
        event.stopPropagation()
        setSelectedItem({ type: 'edge', data: d.rawData })
      })

    const linkLabels = g.append('g')
      .selectAll('text')
      .data(edges)
      .enter().append('text')
      .text(d => (d as any).name)
      .attr('font-size', '8px')
      .attr('fill', 'rgba(255,255,255,0.2)')
      .attr('text-anchor', 'middle')
      .attr('font-weight', '900')
      .attr('letter-spacing', '0.1em')
      .style('text-transform', 'uppercase')
      .style('display', showEdgeLabels ? 'block' : 'none')

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .enter().append('g')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event: any, d: any) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (event: any, d: any) => { d.fx = event.x; d.fy = event.y })
        .on('end', (event: any, d: any) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null }) as any
      )
      .on('click', (event: any, d: any) => {
        event.stopPropagation()
        setSelectedItem({ type: 'node', data: d.rawData, entityType: d.type, color: getColor(d.type) })
      })

    node.append('circle')
      .attr('r', 14)
      .attr('fill', (d: any) => getColor(d.type))
      .attr('fill-opacity', 0.2)
      .attr('stroke', (d: any) => getColor(d.type))
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.8)

    node.append('circle')
      .attr('r', 4)
      .attr('fill', '#fff')
      .attr('filter', 'drop-shadow(0 0 4px rgba(255,255,255,0.5))')

    node.append('text')
      .text((d: any) => d.name)
      .attr('dx', 20)
      .attr('dy', 5)
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.7)')
      .attr('font-weight', '700')
      .style('pointer-events', 'none')

    simulation.on('tick', () => {
      link.attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y).attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y)
      linkLabels.attr('x', (d: any) => (d.source.x + d.target.x) / 2).attr('y', (d: any) => (d.source.y + d.target.y) / 2)
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    svg.on('click', () => setSelectedItem(null))
    return () => {
      simulation.stop()
    }
  }, [graphData, getColor, showEdgeLabels])

  const handleZoom = (direction: 'in' | 'out' | 'reset') => {
    if (!svgRef.current || !zoomRef.current) return
    const svg = svgRef.current
    const zoom = zoomRef.current

    if (direction === 'reset') {
      svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity)
    } else {
      const factor = direction === 'in' ? 1.5 : 0.6
      svg.transition().duration(500).call(zoom.scaleBy, factor)
    }
  }

  return (
    <div className="relative w-full h-full bg-[#07080C] overflow-hidden group">
      {/* Background Matrix Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Control Overlay */}
      <div className="absolute top-0 left-0 right-0 p-6 z-10 flex justify-between items-start pointer-events-none">
        <div className="space-y-1 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/20 border border-[var(--accent)]/30 flex items-center justify-center text-[var(--accent)] shadow-[0_0_15px_rgba(var(--accent-rgb),0.2)]">
              <Database className="w-4 h-4" />
            </div>
            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/80">Neural Connectivity Grid</h3>
          </div>
          <p className="text-[9px] text-white/20 font-mono tracking-widest uppercase ml-11">Causal Link Discovery Engine</p>
        </div>

        <div className="flex items-center gap-3 pointer-events-auto">
          <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-xl p-1">
            <button
              onClick={() => handleZoom('in')}
              className="p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-all outline-none"
              title="Zoom In"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleZoom('out')}
              className="p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-all outline-none"
              title="Zoom Out"
            >
              <Minus className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-white/10 mx-1" />
            <button
              onClick={() => handleZoom('reset')}
              className="p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-all outline-none"
              title="Reset View"
            >
              <Target className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-xl p-1 ml-2">
            <button
              onClick={() => setShowEdgeLabels(!showEdgeLabels)}
              className={cn(
                "p-2 rounded-lg transition-all",
                showEdgeLabels ? "bg-[var(--accent)] text-[#07080C] shadow-lg" : "text-white/20 hover:text-white/40"
              )}
              title="Toggle Labels"
            >
              {showEdgeLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="h-10 px-5 bg-white/5 border border-white/10 rounded-xl flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-white/50 hover:bg-white/10 hover:text-white transition-all disabled:opacity-20 active:scale-95 shadow-xl ml-2"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin text-[var(--accent)]")} />
            Sync
          </button>

          {onToggleMaximize && (
            <button
              onClick={onToggleMaximize}
              className="w-10 h-10 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center text-white/20 hover:text-white hover:bg-white/10 transition-all active:scale-95"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div ref={graphContainerRef} className="w-full h-full" />

      {/* Empty/Loading States */}
      <AnimatePresence>
        {!graphData && !loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <Activity className="w-12 h-12 text-white/5 mb-4 animate-pulse stroke-1" />
            <span className="text-[9px] font-black uppercase tracking-[0.5em] text-white/10">Synchronizing Neural Channels...</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Legends & Hints */}
      <div className="absolute bottom-6 left-6 flex flex-col gap-4 max-w-xs z-10 pointer-events-none">
        {(currentPhase === 1 || isSimulating) && (
          <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="flex items-center gap-3 px-4 py-3 bg-[var(--accent)]/[0.08] border border-[var(--accent)]/30 rounded-2xl backdrop-blur-md">
            <Zap className="w-3.5 h-3.5 text-[var(--accent)] animate-pulse" />
            <span className="text-[9px] font-black text-white/60 uppercase tracking-widest leading-none">GraphRAG LSTM: Synchronizing Buffer...</span>
          </motion.div>
        )}

        {graphData && entityTypes.length > 0 && (
          <div className="glass-card !bg-black/40 !p-5 border-white/10 shadow-2xl pointer-events-auto">
            <h4 className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <Layers className="w-3 h-3" /> Entity Schemas
            </h4>
            <div className="flex flex-wrap gap-3">
              {entityTypes.map(type => (
                <div key={type.name} className="flex items-center gap-2 bg-white/5 px-2.5 py-1.5 rounded-lg border border-white/5 group hover:border-white/10 transition-colors">
                  <div className="w-2 h-2 rounded-full shadow-[0_0_8px_rgba(var(--accent-rgb),0.5)]" style={{ background: type.color }} />
                  <span className="text-[9px] font-bold text-white/50 uppercase tracking-tighter group-hover:text-white/80 transition-colors">{type.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Detail Inspector */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            className="absolute top-24 right-6 w-80 glass-card !p-0 shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-white/10 z-20 flex flex-col overflow-hidden"
          >
            <div className="flex justify-between items-center px-5 py-4 border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <Info className="w-4 h-4 text-[var(--accent)]" />
                <span className="text-[10px] font-black uppercase tracking-widest text-white/70">
                  {selectedItem.type === 'node' ? 'Entity Snapshot' : 'Logical Relation'}
                </span>
              </div>
              <button onClick={() => setSelectedItem(null)} className="w-8 h-8 flex items-center justify-center text-white/20 hover:text-white hover:bg-white/5 rounded-lg transition-all text-xl mt-[-4px]">×</button>
            </div>

            <div className="p-6 space-y-6 overflow-y-auto scrollable max-h-[60vh]">
              {selectedItem.type === 'node' ? (
                <>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[8px] font-black text-white/40 uppercase tracking-widest" style={{ color: selectedItem.color, borderColor: `${selectedItem.color}33` }}>
                        {selectedItem.entityType}
                      </span>
                    </div>
                    <h2 className="text-xl font-black text-white leading-tight tracking-tight uppercase">{selectedItem.data.name}</h2>
                    <span className="text-[8px] font-mono text-white/10 uppercase tracking-widest block">{selectedItem.data.uuid}</span>
                  </div>

                  {selectedItem.data.summary && (
                    <div className="p-4 rounded-xl bg-white/[0.02] border-l-2 border-[var(--accent)] text-[11px] text-white/50 leading-relaxed italic">
                      {selectedItem.data.summary}
                    </div>
                  )}

                  {selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0 && (
                    <div className="space-y-3">
                      <h5 className="text-[9px] font-black text-white/20 uppercase tracking-[0.3em]">Data Attributes</h5>
                      <div className="space-y-2">
                        {Object.entries(selectedItem.data.attributes).map(([k, v]) => (
                          <div key={k} className="flex justify-between items-center p-3 rounded-lg bg-white/[0.01] border border-white/5">
                            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">{k}</span>
                            <span className="text-[10px] font-bold text-white/70">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-6">
                  <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col items-center text-center gap-3">
                    <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">{selectedItem.data.source_name}</span>
                    <div className="w-px h-6 bg-white/10" />
                    <div className="px-4 py-2 rounded-xl bg-[var(--accent)]/10 border border-[var(--accent)] text-[var(--accent)] text-[10px] font-black tracking-widest uppercase">
                      {selectedItem.data.name || 'RELATED_TO'}
                    </div>
                    <div className="w-px h-6 bg-white/10" />
                    <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">{selectedItem.data.target_name}</span>
                  </div>

                  {selectedItem.data.fact && (
                    <div className="space-y-2">
                      <h5 className="text-[9px] font-black text-white/20 uppercase tracking-[0.3em]">Relation Context</h5>
                      <p className="p-4 rounded-xl bg-white/[0.01] border border-white/5 text-[11px] text-white/60 leading-relaxed indent-4 uppercase">
                        {selectedItem.data.fact}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-white/5 bg-white/[0.01] flex justify-center">
              <button className="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-[var(--accent)] hover:text-white transition-colors">
                Deep Inspection Node <Share2 className="w-3 h-3" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default GraphPanel
