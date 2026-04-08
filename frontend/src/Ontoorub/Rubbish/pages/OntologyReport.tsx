import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { reportApi, simulationApi, graphApi } from '../api/ontology'

interface LogEntry {
  time: string
  message: string
  type: 'info' | 'success' | 'error' | 'warning'
}

interface ReportOutline {
  title: string
  summary: string
  sections: Array<{ title: string; description?: string }>
}

interface AgentLog {
  timestamp: number
  action: string
  details?: Record<string, any>
  section_index?: number
  section_title?: string
}

const STEPS = [
  { num: 1, title: 'Graph Construction', icon: '⬡' },
  { num: 2, title: 'Environment Setup', icon: '⚙' },
  { num: 3, title: 'Simulation', icon: '▶' },
  { num: 4, title: 'Report', icon: '📊' },
  { num: 5, title: 'Interaction', icon: '💬' },
]

export const OntologyReport: React.FC = () => {
  const { reportId: routeReportId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const logEndRef = useRef<HTMLDivElement>(null)

  // Get params from URL
  const projectId = searchParams.get('projectId') || ''
  const graphId = searchParams.get('graphId') || ''
  const simulationIdParam = searchParams.get('simulationId') || ''

  // State
  const [reportId, setReportId] = useState(routeReportId || '')
  const [simulationId, setSimulationId] = useState(simulationIdParam)
  const [currentStep, setCurrentStep] = useState(4)
  const [status, setStatus] = useState<'processing' | 'completed' | 'error'>('processing')

  // Report state
  const [reportOutline, setReportOutline] = useState<ReportOutline | null>(null)
  const [generatedSections, setGeneratedSections] = useState<Record<number, string>>({})
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0)
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set())
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [lastLogLine, setLastLogLine] = useState(0)

  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([])

  // Helpers
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [...prev, { time, message, type }])
  }, [])

  const scrollToLogEnd = useCallback(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToLogEnd() }, [logs, scrollToLogEnd])

  // Load report data
  useEffect(() => {
    if (reportId) {
      loadReportData()
    } else if (simulationId) {
      startReportGeneration()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId, simulationId])

  const loadReportData = async () => {
    try {
      addLog(`Loading report: ${reportId}`, 'info')
      const res = await reportApi.get(reportId)
      if (res.data.success && res.data.data) {
        const reportData = res.data.data
        setReportOutline(reportData.outline)
        setGeneratedSections(reportData.sections || {})
        if (reportData.simulation_id) {
          setSimulationId(reportData.simulation_id)
        }
        if (reportData.status === 'completed') {
          setStatus('completed')
          addLog('Report loaded successfully', 'success')
        }
      }
    } catch (err: any) {
      addLog(`Failed to load report: ${err.message}`, 'error')
    }
  }

  const startReportGeneration = async () => {
    if (!simulationId) return

    addLog('Starting report generation...', 'info')
    setStatus('processing')

    try {
      const res = await reportApi.generate({
        simulation_id: simulationId,
        project_id: projectId,
        graph_id: graphId,
      })

      if (res.data.success && res.data.data?.report_id) {
        setReportId(res.data.data.report_id)
        addLog(`Report task created: ${res.data.data.report_id}`, 'success')
        pollReportStatus(res.data.data.report_id)
      }
    } catch (err: any) {
      addLog(`Report generation failed: ${err.message}`, 'error')
      setStatus('error')
    }
  }

  const fetchReportUpdate = useCallback(async () => {
    if (!reportId) return
    try {
      // Poll agent logs
      const logRes = await reportApi.getAgentLog(reportId, lastLogLine)
      if (logRes.data.success && logRes.data.data?.logs) {
        const newLogs = logRes.data.data.logs
        if (newLogs.length > 0) {
          setAgentLogs(prev => [...prev, ...newLogs])
          setLastLogLine(prev => prev + newLogs.length)
          processLogs(newLogs)
        }
      }

      // Check status
      const statusRes = await reportApi.getStatus({ task_id: reportId })
      if (statusRes.data.success && statusRes.data.data) {
        const data = statusRes.data.data
        if (data.status === 'completed') {
          setStatus('completed')
          addLog('Report status refreshed: Completed', 'success')
          loadReportData()
        } else if (data.status === 'failed') {
          setStatus('error')
          addLog('Report status refreshed: Failed', 'error')
        }
      }
    } catch (err) { /* continue */ }
  }, [reportId, lastLogLine, addLog])

  const manualRefresh = () => {
    fetchReportUpdate();
  };

  const pollReportStatus = (rId: string) => {
    // Initial fetch
    fetchReportUpdate();
    // REMOVED: Auto-polling interval disabled per requirements
  }

  const processLogs = (newLogs: AgentLog[]) => {
    for (const log of newLogs) {
      if (log.action === 'planning_complete' && log.details?.outline) {
        setReportOutline(log.details.outline)
        addLog('Report outline generated', 'success')
      } else if (log.action === 'section_start') {
        setCurrentSectionIndex(log.section_index || 0)
        addLog(`Generating section ${log.section_index}: ${log.section_title}`, 'info')
      } else if (log.action === 'section_content' && log.section_index) {
        setGeneratedSections(prev => ({
          ...prev,
          [log.section_index!]: log.details?.content || ''
        }))
      }
    }
  }

  const toggleSectionCollapse = (idx: number) => {
    setCollapsedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(idx)) {
        newSet.delete(idx)
      } else {
        newSet.add(idx)
      }
      return newSet
    })
  }

  const isSectionCompleted = (idx: number) => {
    return generatedSections[idx] !== undefined
  }

  const goToInteraction = () => {
    navigate(`/ontology/interaction/${reportId}?projectId=${projectId}&graphId=${graphId}&simulationId=${simulationId}`)
  }

  const completedSections = Object.keys(generatedSections).length
  const totalSections = reportOutline?.sections?.length || 0

  return (
    <div className="h-screen bg-[#0F1117] text-[#F5F0EB] font-['Inter',sans-serif] flex flex-col overflow-hidden">
      {/* Workflow Stepper */}
      <nav className="h-[60px] bg-[#161822] border-b border-[rgba(250,212,192,0.12)] flex items-center px-8 shrink-0">
        <div className="flex items-center gap-8">
          <div className="font-extrabold text-xl tracking-wider text-[#FAD4C0] cursor-pointer" onClick={() => navigate(-1)}>AARAMBH</div>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-1.5">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.num}>
                <div
                  className={`flex items-center gap-3 px-4 py-1.5 rounded-full text-[10px] font-mono font-black uppercase tracking-widest transition-all border ${step.num === currentStep
                      ? 'bg-[#FAD4C0] text-[#111827] border-[#FAD4C0]'
                      : step.num < currentStep
                        ? 'bg-[#16A34A]/10 text-[#16A34A] border-[#16A34A]/20'
                        : 'bg-white/5 text-white/20 border-white/5 opacity-50'
                    }`}
                >
                  <span className="opacity-50 group-hover:opacity-100">{step.icon}</span>
                  <span>{step.title}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="w-4 h-px bg-white/5" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </nav>

      <main className="flex-1 overflow-hidden p-10 flex gap-10">
        {/* Left - Report Panel */}
        <div className="flex-1 flex flex-col bg-[#161822] border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
          <div className="px-10 py-6 border-b border-white/5 flex items-center justify-between bg-[#1A1C2A]/30 shrink-0">
            <div className="flex items-center gap-4">
              <span className="text-[10px] font-mono font-black text-white uppercase tracking-widest italic">INTELLIGENCE_OUTPUT_STREAM</span>
              <span className="text-[9px] font-mono text-white/20 uppercase tracking-widest">{completedSections}/{totalSections} CHUNKS_SYNCED</span>
            </div>
            <button
              onClick={manualRefresh}
              className="px-5 py-2 bg-[#FAD4C0]/5 border border-[#FAD4C0]/20 text-[#FAD4C0] text-[9px] font-mono font-bold uppercase rounded hover:bg-[#FAD4C0] hover:text-[#111827] transition-all"
            >
              Manual_Sync
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-12 space-y-12 scrollbar-thin scrollbar-thumb-white/5 selection:bg-[#FAD4C0] selection:text-[#111827]">
            {reportOutline ? (
              <article className="max-w-3xl mx-auto space-y-16">
                {/* Executive Summary Header */}
                <header className="space-y-6">
                  <div className="flex items-center gap-4">
                    <span className="px-3 py-1 bg-[#FAD4C0]/10 text-[#FAD4C0] text-[9px] font-mono font-black rounded-lg border border-[#FAD4C0]/20 uppercase">Core_Prediction_Report</span>
                    <span className="text-[9px] font-mono text-white/20 uppercase">REF_ID: {reportId?.slice(0, 8) || 'PENDING'}</span>
                  </div>
                  <h1 className="text-4xl font-black text-white tracking-tight leading-tight uppercase font-mono italic">{reportOutline.title}</h1>
                  <p className="text-lg text-[#A8A3B3] leading-relaxed font-medium pb-10 border-b border-white/5 italic">
                    {reportOutline.summary}
                  </p>
                </header>

                {/* Sub-sections */}
                <section className="space-y-8 pb-20">
                  {reportOutline.sections.map((section, idx) => (
                    <div
                      key={idx}
                      className={`border rounded-3xl overflow-hidden transition-all ${currentSectionIndex === idx + 1
                          ? 'border-[#FAD4C0]/40 bg-[#FAD4C0]/5'
                          : isSectionCompleted(idx + 1)
                            ? 'border-white/5 bg-[#0F1117]/50'
                            : 'border-white/5 opacity-40'
                        }`}
                    >
                      <div
                        onClick={() => isSectionCompleted(idx + 1) && toggleSectionCollapse(idx)}
                        className={`flex items-center gap-6 px-8 py-6 ${isSectionCompleted(idx + 1) ? 'cursor-pointer hover:bg-white/5' : ''
                          }`}
                      >
                        <span className={`text-[10px] font-mono font-black ${isSectionCompleted(idx + 1) ? 'text-[#16A34A]' : 'text-white/20'
                          }`}>
                          VECTOR_{String(idx + 1).padStart(2, '0')}
                        </span>
                        <h3 className="text-xs font-black text-white uppercase tracking-widest flex-1 italic">{section.title}</h3>
                        {isSectionCompleted(idx + 1) && (
                          <div className={`transition-transform duration-300 ${collapsedSections.has(idx) ? 'rotate-180' : ''}`}>
                            <span className="text-white/20">↓</span>
                          </div>
                        )}
                      </div>

                      {!collapsedSections.has(idx) && (
                        <div className="px-10 py-10 border-t border-white/5 bg-[#1A1C2B]/20">
                          {generatedSections[idx + 1] ? (
                            <div className="space-y-6">
                              {generatedSections[idx + 1].split('\n').map((p, i) => (
                                <p key={i} className="text-sm text-[#F5F0EB]/80 leading-relaxed font-medium">
                                  {p}
                                </p>
                              ))}
                            </div>
                          ) : currentSectionIndex === idx + 1 ? (
                            <div className="flex items-center gap-4 py-6">
                              <div className="w-5 h-5 border-2 border-[#FAD4C0] border-t-transparent rounded-full animate-spin" />
                              <span className="text-[10px] font-mono text-[#FAD4C0] uppercase animate-pulse">Syncing_Vectors: {section.title}...</span>
                            </div>
                          ) : (
                            <div className="text-white/10 font-mono text-[10px] uppercase italic">Awaiting_Compute_Allocation...</div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              </article>
            ) : (
              <div className="h-full flex flex-col items-center justify-center gap-8">
                <div className="relative">
                  <div className="absolute inset-0 bg-[#FAD4C0]/20 rounded-full animate-ping" />
                  <div className="w-20 h-20 bg-[#161822] border border-[#FAD4C0]/30 rounded-full flex items-center justify-center shadow-2xl">
                    <span className="text-2xl">📊</span>
                  </div>
                </div>
                <div className="text-center space-y-2">
                  <h2 className="text-xs font-mono font-black text-white uppercase tracking-widest animate-pulse">Initializing_Report_Matrix</h2>
                  <p className="text-[9px] font-mono text-white/20 uppercase tracking-widest">Waiting for neural report agent...</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right - Mission Command */}
        <div className="w-[450px] flex flex-col gap-8 shrink-0">
          {/* Summary Tool */}
          <div className="border border-white/5 bg-[#161822] rounded-3xl p-8 space-y-8 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-[10px] font-mono font-black text-[#FAD4C0] uppercase tracking-widest italic">COMPUTE_STATUS</h3>
              <div className={`flex items-center gap-3 bg-[#0F1117] border border-white/5 px-4 py-1.5 rounded-full`}>
                <span className={`w-1.5 h-1.5 rounded-full ${status === 'completed' ? 'bg-[#16A34A]' :
                    status === 'error' ? 'bg-red-500' : 'bg-[#FAD4C0] animate-pulse'
                  }`} />
                <span className="text-[9px] font-mono font-black text-white uppercase">{status}</span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-[9px] font-mono text-white/30 uppercase">
                <span>Sync_Coverage</span>
                <span className="text-white">{totalSections > 0 ? Math.round((completedSections / totalSections) * 100) : 0}%</span>
              </div>
              <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#FAD4C0] transition-all duration-700 shadow-[0_0_10px_rgba(250,212,192,0.4)]"
                  style={{ width: `${totalSections > 0 ? (completedSections / totalSections) * 100 : 0}%` }}
                />
              </div>
            </div>

            {status === 'completed' && (
              <button
                onClick={goToInteraction}
                className="w-full py-5 bg-[#FAD4C0] text-[#111827] rounded-2xl font-mono font-black text-xs uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-4"
              >
                Neural_Interaction_Start
                <span>→</span>
              </button>
            )}
          </div>

          {/* Activity Log Cluster */}
          <div className="flex-1 flex flex-col min-h-0 bg-[#161822] border border-white/5 rounded-3xl overflow-hidden divide-y divide-white/5">
            <section className="flex-1 flex flex-col min-h-0">
              <div className="px-8 py-5 flex items-center justify-between shrink-0 bg-[#0F1117]/30">
                <div className="flex items-center gap-3">
                  <span className="text-purple-400">🤖</span>
                  <span className="text-[9px] font-mono font-black text-white/40 uppercase tracking-widest">Neural_Activity_Trace</span>
                </div>
              </div>
              <div className="flex-1 p-8 overflow-y-auto space-y-3 bg-[#0c0c14] scrollbar-none">
                {agentLogs.length === 0 && (
                  <span className="text-[9px] font-mono text-white/10 uppercase italic">Awaiting_Agent_Sign-on...</span>
                )}
                {agentLogs.slice(-30).map((log, i) => (
                  <div key={i} className="flex gap-4 group">
                    <span className="text-[8px] font-mono text-white/10 shrink-0 group-hover:text-purple-400/40 transition-colors">[{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}]</span>
                    <span className="text-[9px] font-mono text-white/40 group-hover:text-white transition-colors">{log.action}: <span className="text-white/20 italic">{log.section_title || log.details?.message || 'NULL_BUFFER'}</span></span>
                  </div>
                ))}
              </div>
            </section>

            <section className="h-1/3 flex flex-col min-h-0">
              <div className="px-8 py-4 flex items-center justify-between shrink-0 bg-[#0F1117]/50">
                <div className="flex items-center gap-3">
                  <span className="text-[#16A34A] text-[8px]">●</span>
                  <span className="text-[9px] font-mono font-black text-white/40 uppercase tracking-widest">Host_Syslog</span>
                </div>
              </div>
              <div className="flex-1 p-8 overflow-y-auto space-y-3 bg-[#0a0a0f] scrollbar-none">
                {logs.slice(-20).map((log, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="text-[8px] font-mono text-white/10 shrink-0">[{log.time}]</span>
                    <span className={`text-[9px] font-mono font-bold tracking-tight ${log.type === 'error' ? 'text-red-500' :
                        log.type === 'success' ? 'text-[#16A34A]' :
                          log.type === 'warning' ? 'text-amber-500' :
                            'text-white/20'
                      }`}>
                      {log.message.toUpperCase()}
                    </span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}

export default OntologyReport
