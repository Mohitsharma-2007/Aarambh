import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'

interface SimAction {
  timestamp: number
  agent_id: string
  agent_name: string
  action_type: string
  platform: string
  round_num: number
  action_args: { content?: string }
}

interface RunStatus {
  simulation_id: string
  status: string
  current_round: number
  max_rounds: number
  total_actions: number
  twitter_actions: number
  reddit_actions: number
}

export const OntologySimulationRun: React.FC = () => {
  const { projectId: simulationId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') || ''
  const graphId = searchParams.get('graphId') || ''
  const maxRounds = parseInt(searchParams.get('maxRounds') || '10')

  const feedRef = useRef<HTMLDivElement>(null)

  const [status, setStatus] = useState<RunStatus | null>(null)
  const [actions, setActions] = useState<SimAction[]>([])
  const [isRunning, setIsRunning] = useState(true)
  const [elapsed, setElapsed] = useState(0)
  const [filter, setFilter] = useState<'all' | 'twitter' | 'reddit'>('all')

  const fetchStatusAndActions = useCallback(async () => {
    if (!simulationId) return
    try {
      const [statusRes, actionsRes] = await Promise.all([
        fetch(`http://localhost:8000/ontology-api/api/simulation/${simulationId}/run-status`),
        fetch(`http://localhost:8000/ontology-api/api/simulation/${simulationId}/actions?limit=100`),
      ])

      const [statusData, actionsData] = await Promise.all([statusRes.json(), actionsRes.json()])

      if (statusData.success) {
        setStatus(statusData.data)
        if (statusData.data.status === 'stopped' || statusData.data.status === 'completed') {
          setIsRunning(false)
        }
      }
      if (actionsData.success) {
        setActions(actionsData.data?.actions || [])
      }
    } catch (err) { /* continue */ }
  }, [simulationId])

  // Initial load
  useEffect(() => {
    fetchStatusAndActions();
  }, [fetchStatusAndActions]);

  const manualRefresh = () => {
    fetchStatusAndActions();
  };

  // Timer
  useEffect(() => {
    if (!isRunning) return
    const timer = setInterval(() => setElapsed(prev => prev + 1), 1000)
    return () => clearInterval(timer)
  }, [isRunning])

  const stopSimulation = async () => {
    try {
      await fetch('http://localhost:5001/api/simulation/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id: simulationId }),
      })
      setIsRunning(false)
    } catch (err) { /* */ }
  }

  const goToReport = () => {
    navigate(`/ontology/report/${simulationId}?projectId=${projectId}&graphId=${graphId}`)
  }

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  }

  const filteredActions = filter === 'all' ? actions : actions.filter(a => a.platform === filter)

  const roundProgress = status ? (status.current_round / status.max_rounds) * 100 : 0

  return (
    <div className="h-screen bg-[#0F1117] text-[#F5F0EB] font-['Inter',sans-serif] flex flex-col overflow-hidden">
      {/* Header */}
      <nav className="h-[60px] bg-[#161822] border-b border-[rgba(250,212,192,0.12)] flex items-center justify-between px-8 shrink-0 text-white">
        <div className="flex items-center gap-6">
          <div
            className="font-extrabold text-xl tracking-wider cursor-pointer text-[#FAD4C0]"
            onClick={() => navigate(-1)}
          >
            AARAMBH
          </div>
          <div className="h-4 w-px bg-white/10" />
          <h1 className="text-[10px] font-mono font-black text-white/40 uppercase tracking-widest italic">Simulation_Active_Sequence</h1>
        </div>

        <div className="flex items-center gap-8">
          <div className="flex flex-col items-end">
            <span className="text-[9px] font-mono text-white/30 uppercase tracking-widest">Elapsed_Time</span>
            <span className="text-sm font-mono font-black text-[#FAD4C0]">{formatTime(elapsed)}</span>
          </div>

          <div className="flex items-center gap-3 bg-[#0F1117] border border-white/5 px-4 py-2 rounded-xl">
            <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-[#16A34A] animate-pulse shadow-[0_0_8px_rgba(22,163,74,0.4)]" : "bg-white/20"}`} />
            <span className="text-[10px] font-mono font-black uppercase tracking-widest text-white">
              {status?.status || "INITIALIZING"}
            </span>
          </div>
        </div>
      </nav>

      <main className="flex-1 overflow-y-auto p-10 space-y-10 scrollbar-thin scrollbar-thumb-white/5">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          {/* Stats Cards */}
          {[
            { label: "ROUND_PTR", value: `${status?.current_round || 0}/${status?.max_rounds || maxRounds}`, color: "#FAD4C0" },
            { label: "TOTAL_VECTORS", value: status?.total_actions || 0, color: "#FFF" },
            { label: "SOCIAL_X", value: status?.twitter_actions || 0, color: "#1DA1F2" },
            { label: "RSS_REDDIT", value: status?.reddit_actions || 0, color: "#FF4500" },
            { label: "LATENCY_BUFFER", value: "0 ms", color: "#16A34A" }
          ].map((stat, i) => (stat.label !== "LATENCY_BUFFER" || status) && (
            <div key={i} className="bg-[#161822] border border-white/5 p-6 rounded-3xl group hover:border-[#FAD4C0]/20 transition-all">
              <div className="text-[9px] font-mono font-black text-white/30 uppercase tracking-widest mb-4 group-hover:text-[#FAD4C0]/50 transition-colors">
                {stat.label}
              </div>
              <div className="text-2xl font-mono font-black" style={{ color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Progress Matrix */}
        <div className="bg-[#161822] border border-[rgba(250,212,192,0.1)] p-8 rounded-3xl space-y-6">
          <div className="flex justify-between items-baseline">
            <span className="text-[9px] font-mono font-black text-[#FAD4C0] uppercase tracking-widest">Global_Simulation_Progress</span>
            <span className="text-xl font-mono font-black text-[#FAD4C0]">{Math.round(roundProgress)}%</span>
          </div>
          <div className="h-1 w-full bg-[#0F1117] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#FAD4C0] transition-all duration-1000 shadow-[0_0_15px_rgba(250,212,192,0.5)]"
              style={{ width: `${roundProgress}%` }}
            />
          </div>
        </div>

        {/* Action Feed Matrix */}
        <div className="bg-[#161822] border border-white/5 rounded-3xl overflow-hidden flex flex-col min-h-[400px]">
          <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-[#1A1C2A]/30">
            <div className="flex items-center gap-6">
              <span className="text-[10px] font-mono font-black text-white uppercase tracking-widest italic">NEURAL_EVENT_STREAM</span>
              <div className="flex gap-2">
                {(['all', 'twitter', 'reddit'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`text-[9px] font-mono font-black px-4 py-1 rounded-full border transition-all uppercase ${filter === f
                        ? 'bg-[#FAD4C0] border-[#FAD4C0] text-[#111827]'
                        : 'border-white/10 text-white/40 hover:border-white/30'
                      }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={manualRefresh}
                className="px-4 py-1.5 bg-[#FAD4C0]/5 border border-[#FAD4C0]/20 text-[#FAD4C0] text-[9px] font-mono font-bold uppercase rounded hover:bg-[#FAD4C0] hover:text-[#111827] transition-all"
              >
                Manual_Sync
              </button>
              <span className="text-[10px] font-mono text-white/20 uppercase">{filteredActions.length} EVENTS_TRACKED</span>
            </div>
          </div>

          <div ref={feedRef} className="flex-1 overflow-y-auto p-10 space-y-4 scrollbar-thin scrollbar-thumb-white/5">
            {filteredActions.length === 0 && (
              <div className="h-40 flex items-center justify-center text-white/10 font-mono text-[11px] uppercase tracking-widest flex-col gap-4">
                <div className="w-12 h-px bg-white/5" />
                {isRunning ? 'Pipeline_Active: Awaiting_Data_Vectors...' : 'No_Actions_Captured'}
                <div className="w-12 h-px bg-white/5" />
              </div>
            )}
            {filteredActions.map((action, i) => (
              <div key={i} className="flex gap-6 p-6 rounded-2xl bg-[#0F1117] border border-white/5 hover:border-[#FAD4C0]/20 transition-all group">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-black shrink-0 shadow-lg ${action.platform === 'twitter' ? 'bg-[#1DA1F2]/10 text-[#1DA1F2] border border-[#1DA1F2]/20' : 'bg-[#FF4500]/10 text-[#FF4500] border border-[#FF4500]/20'
                  }`}>
                  {action.platform === 'twitter' ? '𝕏' : 'R'}
                </div>
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-[11px] font-bold text-white uppercase tracking-wider">{action.agent_name}</span>
                      <span className="text-[9px] font-mono text-[#FAD4C0] bg-[#FAD4C0]/5 px-2 py-0.5 rounded border border-[#FAD4C0]/20">ROUND_{action.round_num}</span>
                    </div>
                    <span className={`text-[10px] font-mono font-black px-2 py-1 rounded-lg uppercase tracking-tight ${action.action_type === 'CREATE_POST' ? 'text-[#16A34A] bg-[#16A34A]/5' :
                        action.action_type === 'LIKE_POST' ? 'text-[#D81B60] bg-[#D81B60]/5' :
                          action.action_type === 'REPOST' ? 'text-[#00ACC1] bg-[#00ACC1]/5' :
                            'text-white/40 bg-white/5'
                      }`}>
                      {action.action_type}
                    </span>
                  </div>
                  {action.action_args?.content && (
                    <p className="text-xs text-[#A8A3B3] leading-relaxed line-clamp-3 font-medium opacity-80 group-hover:opacity-100 transition-opacity">
                      {action.action_args.content}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Global Control Bar */}
        <div className="flex items-center justify-between gap-10 pt-4 pb-10">
          <button
            onClick={stopSimulation}
            disabled={!isRunning}
            className="px-10 py-5 bg-red-500/10 hover:bg-red-500 border border-red-500/20 rounded-2xl text-red-500 hover:text-white text-xs font-mono font-black uppercase tracking-[0.2em] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
          >
            Abort_Sequence
          </button>

          <button
            onClick={goToReport}
            disabled={isRunning}
            className={`flex-1 py-5 rounded-2xl font-mono font-black text-xs uppercase tracking-[0.3em] flex justify-center items-center gap-4 transition-all ${!isRunning
                ? "bg-[#FAD4C0] text-[#111827] shadow-xl hover:scale-[1.02]"
                : "bg-white/5 text-white/10 border border-white/5 cursor-not-allowed"
              }`}
          >
            <span>Proceed_To_Intelligence_Report</span>
            <span className={!isRunning ? "translate-x-0" : "opacity-0"}>→</span>
          </button>
        </div>
      </main>
    </div>
  )
}

export default OntologySimulationRun
