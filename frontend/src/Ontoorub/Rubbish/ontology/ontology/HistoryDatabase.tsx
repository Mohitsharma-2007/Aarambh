import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  History, Database, Folder, FileText, 
  Terminal, ChevronRight, Search, Zap,
  Activity, Clock, Layers
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { simulationApi } from '../../api/ontology'
import { cn } from '@/utils/cn'

interface ProjectFile {
  filename: string
  path?: string
}

interface Project {
  simulation_id: string
  project_id?: string
  report_id?: string
  simulation_requirement?: string
  files?: ProjectFile[]
  created_at?: string
  current_round?: number
  total_rounds?: number
}

interface HistoryDatabaseProps {
  onSelectProject?: (project: Project) => void
}

const FILE_TYPE_COLORS: Record<string, { bg: string; color: string }> = {
  pdf: { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' },
  doc: { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' },
  docx: { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' },
  xls: { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981' },
  xlsx: { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981' },
  csv: { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981' },
  ppt: { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' },
  pptx: { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' },
  txt: { bg: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255,255,255,0.5)' },
  md: { bg: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255,255,255,0.5)' },
  json: { bg: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' },
  other: { bg: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255,255,255,0.3)' },
}

export const HistoryDatabase: React.FC<HistoryDatabaseProps> = ({ onSelectProject }) => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true)
      const response = await simulationApi.getHistory()
      if (response.data?.success) setProjects(response.data.data || [])
    } catch (error) {
      setProjects([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    if (!containerRef.current) return
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => setIsExpanded(entry.isIntersecting))
    }, { threshold: 0.5, rootMargin: '0px' })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    return new Date(dateStr).toISOString().slice(0, 10)
  }

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }

  const getCardStyle = (index: number) => {
    const total = projects.length
    if (isExpanded) {
      const col = index % 4
      const row = Math.floor(index / 4)
      const x = (col - 1.5) * 310
      const y = 20 + row * 320
      return { transform: `translate(${x}px, ${y}px) rotate(0deg) scale(1)`, zIndex: 100 + index, opacity: 1 }
    } else {
      const centerIndex = (total - 1) / 2
      const offset = index - centerIndex
      const x = offset * 40
      const y = 20 + Math.abs(offset) * 10
      const r = offset * 4
      const s = 1 - Math.abs(offset) * 0.05
      return { transform: `translate(${x}px, ${y}px) rotate(${r}deg) scale(${s})`, zIndex: 10 + index, opacity: 1 }
    }
  }

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center gap-6 text-white/20">
        <Activity className="w-8 h-8 animate-pulse text-[var(--accent)]" />
        <span className="text-[10px] font-black uppercase tracking-[0.4em]">Decryption Protocol Initialized...</span>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative w-full mt-20 py-10 overflow-visible text-white/90 font-sans">
      
      {/* Dynamic Background Matrix */}
      {projects.length > 0 && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px)',
            backgroundSize: '80px 80px',
          }} />
        </div>
      )}

      {/* Futuristic Header */}
      <div className="relative z-10 flex items-center justify-center gap-8 mb-12 px-10">
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        <div className="flex flex-col items-center gap-2">
          <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.5em]">Synthetic Memory Archives</span>
          <div className="flex items-center gap-3">
             <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
             <span className="text-xl font-black italic uppercase tracking-tighter font-mono">Deduction Index</span>
          </div>
        </div>
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </div>

      {projects.length > 0 ? (
        <div className="relative flex justify-center items-start px-10 transition-all duration-1000"
          style={{ minHeight: isExpanded ? `${Math.ceil(projects.length / 4) * 320 + 60}px` : '450px' }}
        >
          {projects.map((project, index) => (
            <motion.div
              key={project.simulation_id}
              className={cn(
                "absolute w-[290px] h-[300px] glass-card cursor-pointer group transition-all duration-500 hover:z-[2000] !p-0",
                selectedProject?.simulation_id === project.simulation_id && "border-[var(--accent)] shadow-[0_0_40px_rgba(var(--accent-rgb),0.2)]"
              )}
              style={getCardStyle(index)}
              onClick={() => { setSelectedProject(project); onSelectProject?.(project) }}
            >
              <div className="p-4 flex flex-col h-full bg-gradient-to-br from-white/[0.02] to-transparent">
                <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-3">
                  <span className="text-[9px] font-black font-mono text-white/30 uppercase tracking-widest">
                    ID: {project.simulation_id.slice(4, 12).toUpperCase()}
                  </span>
                  <div className="flex gap-1.5 opacity-50 group-hover:opacity-100 transition-opacity">
                    <div className={cn("w-1.5 h-1.5 rounded-full", project.project_id ? "bg-blue-400 shadow-[0_0_5px_rgba(96,165,250,0.5)]" : "bg-white/10")} />
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-[0_0_5px_rgba(251,191,36,0.5)]" />
                    <div className={cn("w-1.5 h-1.5 rounded-full", project.report_id ? "bg-emerald-400 shadow-[0_0_5px_rgba(16,185,129,0.5)]" : "bg-white/10")} />
                  </div>
                </div>

                <div className="flex-1 space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-xs font-black text-white leading-tight uppercase group-hover:text-[var(--accent)] transition-colors">
                      {project.simulation_requirement?.slice(0, 45) || 'Neural Kernel Load'}...
                    </h3>
                    <p className="text-[10px] text-white/40 leading-relaxed font-medium italic line-clamp-2">
                      {project.simulation_requirement}
                    </p>
                  </div>

                  <div className="flex flex-col gap-1.5 opacity-60 group-hover:opacity-100 transition-all">
                    {(project.files || []).slice(0, 2).map((f, i) => (
                      <div key={i} className="flex items-center gap-2 p-1.5 rounded-lg bg-white/5 border border-white/5 group/file">
                        <FileText className="w-3 h-3 text-white/20 group-hover/file:text-[var(--accent)]" />
                        <span className="text-[9px] text-white/50 truncate font-mono">{f.filename}</span>
                      </div>
                    ))}
                    {project.files && project.files.length > 2 && (
                       <span className="text-[8px] font-black text-white/20 uppercase ml-1">+{project.files.length - 2} NODES</span>
                    )}
                  </div>
                </div>

                <div className="mt-auto pt-4 border-t border-white/5 flex justify-between items-end">
                   <div className="flex flex-col">
                      <span className="text-[8px] font-mono text-white/20">{formatDate(project.created_at)}</span>
                      <span className="text-[10px] font-black font-mono text-[var(--accent)]/60">{formatTime(project.created_at)}</span>
                   </div>
                   <div className="text-right">
                      <span className="text-[8px] font-black uppercase text-white/20 tracking-wider">Protocol Round</span>
                      <div className="text-[11px] font-black font-mono italic">{project.current_round || 0} / {project.total_rounds || '??'}</div>
                   </div>
                </div>
              </div>
              <div className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent w-0 group-hover:w-full transition-all duration-700 ease-in-out" />
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-24 text-white/10">
          <Database className="w-16 h-16 mx-auto mb-6 opacity-20 stroke-1 animate-pulse" />
          <p className="text-[9px] font-black uppercase tracking-[0.5em]">Neural Reservoir Empty</p>
        </div>
      )}

      {/* Detail Protocol Overlay */}
      <AnimatePresence>
        {selectedProject && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-xl flex items-center justify-center z-[10000] p-6 lg:p-20"
            onClick={() => setSelectedProject(null)}
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }}
              className="glass-card w-full max-w-4xl max-h-full overflow-y-auto !p-0 border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.8)]"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex justify-between items-center px-10 py-8 border-b border-white/10 bg-white/[0.02]">
                <div className="flex items-center gap-6">
                  <div className="w-14 h-14 rounded-2xl bg-[var(--accent)]/10 text-[var(--accent)] flex items-center justify-center border border-[var(--accent)]/20 shadow-[0_0_20px_rgba(var(--accent-rgb),0.1)]">
                    <History className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.4em]">Protocol Execution Log</span>
                    <h2 className="text-2xl font-black tracking-tight text-white uppercase italic">{selectedProject.simulation_id.slice(0, 16)}</h2>
                  </div>
                </div>
                <button onClick={() => setSelectedProject(null)} className="w-12 h-12 flex items-center justify-center text-white/20 hover:text-white hover:bg-white/5 rounded-2xl transition-all text-2xl">×</button>
              </div>

              <div className="p-10 grid grid-cols-1 lg:grid-cols-2 gap-10">
                <div className="space-y-8">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 mb-2">
                       <Terminal className="w-4 h-4 text-emerald-400" />
                       <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Requirement Kernel</span>
                    </div>
                    <div className="p-6 rounded-2xl bg-black/40 border border-white/5 text-sm text-white/70 leading-relaxed font-medium italic border-l-2 border-emerald-500/50">
                      "{selectedProject.simulation_requirement}"
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                     <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1">
                        <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">Active Cycle</span>
                        <span className="text-xl font-black font-mono">{selectedProject.current_round || 0} ROUNDS</span>
                     </div>
                     <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col gap-1">
                        <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">Created Temporal</span>
                        <span className="text-lg font-black font-mono text-[var(--accent)]">{formatDate(selectedProject.created_at)}</span>
                     </div>
                  </div>
                </div>

                <div className="space-y-8">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                       <Layers className="w-4 h-4 text-blue-400" />
                       <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Logical Documents</span>
                    </div>
                    <div className="space-y-2 max-h-[300px] overflow-y-auto scrollable pr-2">
                      {selectedProject.files?.map((f, i) => (
                        <div key={i} className="flex items-center gap-4 p-4 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-all group">
                          <div className={cn("p-2 rounded-lg", (FILE_TYPE_COLORS[f.filename.split('.').pop() || ''] || FILE_TYPE_COLORS.other).bg)}>
                             <FileText className="w-4 h-4" style={{ color: (FILE_TYPE_COLORS[f.filename.split('.').pop() || ''] || FILE_TYPE_COLORS.other).color }} />
                          </div>
                          <span className="text-[11px] font-bold text-white/60 truncate flex-1 uppercase">{f.filename}</span>
                          <Zap className="w-3 h-3 text-white/10 group-hover:text-[var(--accent)] transition-colors" />
                        </div>
                      )) || <div className="p-10 text-center opacity-10">NO DATA NODES FOUND</div>}
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-10 bg-white/[0.01] border-t border-white/5">
                <div className="grid grid-cols-3 gap-6">
                   <button onClick={() => { if (selectedProject.project_id) navigate(`/ontology/process/${selectedProject.project_id}`) }} disabled={!selectedProject.project_id}
                      className="flex flex-col items-center gap-3 p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group disabled:opacity-20">
                      <Database className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Step 1: Graph Build</span>
                   </button>
                   <button onClick={() => navigate(`/ontology/simulation/${selectedProject.simulation_id}`)}
                      className="flex flex-col items-center gap-3 p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-amber-500/50 hover:bg-amber-500/5 transition-all group">
                      <Zap className="w-6 h-6 text-amber-400 group-hover:scale-110 transition-transform" />
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Step 2: Simulation</span>
                   </button>
                   <button onClick={() => { if (selectedProject.report_id) navigate(`/ontology/report/${selectedProject.report_id}`) }} disabled={!selectedProject.report_id}
                      className="flex flex-col items-center gap-3 p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all group disabled:opacity-20">
                      <Activity className="w-6 h-6 text-emerald-400 group-hover:scale-110 transition-transform" />
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Step 4: Insights</span>
                   </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default HistoryDatabase
