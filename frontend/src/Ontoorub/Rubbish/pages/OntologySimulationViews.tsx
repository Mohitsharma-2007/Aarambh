import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { GraphPanel, Step2EnvSetup, Step3Simulation } from '../components/ontology'
import { graphApi, simulationApi } from '../api/ontology'

interface LogEntry {
  time: string
  message: string
}

interface GraphNode {
  uuid: string
  name: string
  labels: string[]
  attributes?: Record<string, any>
}

interface GraphEdge {
  uuid: string
  source_node_uuid: string
  target_node_uuid: string
  fact_type: string
  name: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  node_count?: number
  edge_count?: number
}

// Step 2: Environment Setup View
export const OntologySimulationView: React.FC = () => {
  const { simulationId: routeSimulationId } = useParams()
  const navigate = useNavigate()

  // Layout State
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('split')

  // Data State
  const [currentSimulationId, setCurrentSimulationId] = useState<string>(routeSimulationId || '')
  const [projectData, setProjectData] = useState<any>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([])
  const [currentStatus, setCurrentStatus] = useState<'processing' | 'completed' | 'error'>('processing')
  const dataLoadingRef = React.useRef(false)

  // Compute layout styles
  const leftPanelStyle = {
    width: viewMode === 'graph' ? '100%' : viewMode === 'workbench' ? '0%' : '50%',
    opacity: viewMode === 'workbench' ? 0 : 1,
    transform: viewMode === 'workbench' ? 'translateX(-20px)' : 'translateX(0)',
  }

  const rightPanelStyle = {
    width: viewMode === 'workbench' ? '100%' : viewMode === 'graph' ? '0%' : '50%',
    opacity: viewMode === 'graph' ? 0 : 1,
    transform: viewMode === 'graph' ? 'translateX(20px)' : 'translateX(0)',
  }

  // Status computed
  const statusClass = currentStatus
  const statusText = currentStatus === 'error' ? 'Error' : currentStatus === 'completed' ? 'Ready' : 'Preparing'

  // Helpers
  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
    setSystemLogs(prev => {
      const newLogs = [...prev, { time, message: msg }]
      if (newLogs.length > 100) newLogs.shift()
      return newLogs
    })
  }, [])

  const updateStatus = useCallback((status: typeof currentStatus) => {
    setCurrentStatus(status)
  }, [])

  // Layout Methods
  const toggleMaximize = (target: 'graph' | 'workbench') => {
    setViewMode(viewMode === target ? 'split' : target)
  }

  const handleGoBack = () => {
    if (projectData?.project_id) {
      navigate(`/ontology/process/${projectData.project_id}`)
    } else {
      navigate('/ontology')
    }
  }

  const handleNextStep = (params: { maxRounds?: number } = {}) => {
    addLog('Entering Step 3: Start Simulation')

    if (params.maxRounds) {
      addLog(`Custom simulation rounds: ${params.maxRounds} rounds`)
    } else {
      addLog('Using auto-configured simulation rounds')
    }

    // Navigate to Step 3
    navigate(`/ontology/simulation/${currentSimulationId}/run${params.maxRounds ? `?maxRounds=${params.maxRounds}` : ''}`)
  }

  // Check and stop running simulation when user returns from Step 3
  const checkAndStopRunningSimulation = async () => {
    if (!currentSimulationId) return

    try {
      const envStatusRes = await simulationApi.getEnvStatus({ simulation_id: currentSimulationId })

      if (envStatusRes.data?.success && envStatusRes.data?.data?.env_alive) {
        addLog('Detected running simulation environment, closing...')

        try {
          const closeRes = await simulationApi.closeEnv({
            simulation_id: currentSimulationId
          })

          if (closeRes.data?.success) {
            addLog('Simulation environment closed')
          } else {
            addLog(`Failed to close simulation: ${closeRes.data?.error || 'Unknown error'}`)
            await forceStopSimulation()
          }
        } catch (closeErr: any) {
          addLog(`Close exception: ${closeErr.message}`)
          await forceStopSimulation()
        }
      }
    } catch (err) {
      console.warn('Check simulation status failed:', err)
    }
  }

  const forceStopSimulation = async () => {
    try {
      const stopRes = await simulationApi.stop({ simulation_id: currentSimulationId })
      if (stopRes.data?.success) {
        addLog('Simulation force stopped')
      }
    } catch (err: any) {
      addLog(`Force stop exception: ${err.message}`)
    }
  }

  // Data Logic
  const loadSimulationData = async () => {
    if (!currentSimulationId || dataLoadingRef.current) return
    dataLoadingRef.current = true
    try {
      addLog(`Connecting to Simulation Node: ${currentSimulationId.slice(0, 8)}...`)

      const simRes = await simulationApi.get(currentSimulationId)
      if (simRes.data?.success && simRes.data?.data) {
        const simData = simRes.data.data
        const isReady = ['ready', 'running', 'completed', 'stopped'].includes(simData.status)

        if (!isReady) {
          addLog('Neural environment pending activation...')
          updateStatus('processing')
          return
        }

        updateStatus('completed')

        if (simData.project_id) {
          const projRes = await graphApi.getProject(simData.project_id)
          if (projRes.data?.success && projRes.data?.data) {
            setProjectData(projRes.data.data)
            addLog(`Project loaded: ${projRes.data.data.project_id}`)

            if (projRes.data.data.graph_id) {
              await loadGraph(projRes.data.data.graph_id)
            }
          }
        }
      }
    } catch (err: any) {
      addLog(`Load exception: ${err.message}`)
    }
  }

  const loadGraph = async (graphId: string) => {
    setGraphLoading(true)
    try {
      const res = await graphApi.getGraphData(graphId)
      if (res.data?.success) {
        setGraphData(res.data.data)
        addLog('Graph data loaded')
      }
    } catch (err: any) {
      addLog(`Graph load failed: ${err.message}`)
    } finally {
      setGraphLoading(false)
    }
  }

  const refreshGraph = () => {
    if (projectData?.graph_id) {
      loadGraph(projectData.graph_id)
    }
  }

  useEffect(() => {
    addLog('SimulationView initialized')
    checkAndStopRunningSimulation()
    loadSimulationData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="h-screen flex flex-col bg-[#07080C] text-white/90 overflow-hidden font-sans">
      {/* Header */}
      <header className="h-[60px] border-b border-white/10 flex items-center justify-between px-6 bg-[#07080C]/80 backdrop-blur-md relative z-10">
        <div className="flex items-center">
          <div
            className="font-mono font-extrabold text-lg tracking-wider cursor-pointer text-white"
            onClick={() => navigate('/ontology')}
          >
            aarambh_
          </div>
        </div>

        <div className="absolute left-1/2 transform -translate-x-1/2 transition-all duration-500">
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/10 shadow-2xl backdrop-blur-xl">
            {(['graph', 'split', 'workbench'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`border-none px-5 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all ${viewMode === mode
                  ? 'bg-[var(--accent)] text-[#07080C] shadow-[0_0_20px_rgba(var(--accent-rgb),0.3)]'
                  : 'bg-transparent text-white/40 hover:text-white/80'
                  }`}
              >
                {{ graph: 'Matrix', split: 'Dual', workbench: 'Nodes' }[mode]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="font-mono font-black text-[9px] text-white/20 uppercase tracking-[0.3em]">Module_02</span>
            <span className="font-black text-[10px] uppercase tracking-widest text-[var(--accent)]">Environment Setup</span>
          </div>
          <div className="w-px h-4 bg-white/10" />
          <span className={`flex items-center gap-2 text-[9px] font-black uppercase tracking-widest ${statusClass === 'error' ? 'text-red-400' :
            statusClass === 'completed' ? 'text-emerald-400' :
              'text-[var(--accent)]'
            }`}>
            <span className={`w-2 h-2 rounded-full shadow-[0_0_10px_currentColor] ${statusClass === 'error' ? 'bg-red-400' :
              statusClass === 'completed' ? 'bg-emerald-400' :
                'bg-[var(--accent)] animate-pulse'
              }`} />
            {statusText}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex relative overflow-hidden">
        {/* Left Panel: Graph */}
        <div
          className="h-full overflow-hidden border-r border-white/10 transition-all duration-300 bg-[#07080C]"
          style={leftPanelStyle}
        >
          <GraphPanel
            graphData={graphData}
            loading={graphLoading}
            currentPhase={2}
            isSimulating={false}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </div>

        {/* Right Panel: Step2 Environment Setup */}
        <div
          className="h-full overflow-hidden transition-all duration-300"
          style={rightPanelStyle}
        >
          <Step2EnvSetup
            simulationId={currentSimulationId}
            projectData={projectData}
            graphData={graphData}
            systemLogs={systemLogs}
            onGoBack={handleGoBack}
            onNextStep={handleNextStep}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        </div>
      </main>
    </div>
  )
}

// Step 3: Start Simulation Run View
export const OntologySimulationRunView: React.FC = () => {
  const { simulationId: routeSimulationId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Layout State
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('split')

  // Data State
  const [currentSimulationId, setCurrentSimulationId] = useState<string>(routeSimulationId || '')
  const [maxRounds, setMaxRounds] = useState<number | null>(searchParams.get('maxRounds') ? parseInt(searchParams.get('maxRounds')!) : null)
  const [minutesPerRound] = useState(30) // Default 30 minutes per round
  const [projectData, setProjectData] = useState<any>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([])
  const [currentStatus, setCurrentStatus] = useState<'processing' | 'completed' | 'error'>('processing')
  const [isSimulating, setIsSimulating] = useState(false)
  const dataLoadingRef = React.useRef(false)

  // Compute layout styles
  const leftPanelStyle = {
    width: viewMode === 'graph' ? '100%' : viewMode === 'workbench' ? '0%' : '50%',
    opacity: viewMode === 'workbench' ? 0 : 1,
    transform: viewMode === 'workbench' ? 'translateX(-20px)' : 'translateX(0)',
  }

  const rightPanelStyle = {
    width: viewMode === 'workbench' ? '100%' : viewMode === 'graph' ? '0%' : '50%',
    opacity: viewMode === 'graph' ? 0 : 1,
    transform: viewMode === 'graph' ? 'translateX(20px)' : 'translateX(0)',
  }

  // Status computed
  const statusClass = currentStatus
  const statusText = currentStatus === 'error' ? 'Error' : currentStatus === 'completed' ? 'Completed' : isSimulating ? 'Simulating' : 'Ready'

  // Helpers
  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
    setSystemLogs(prev => {
      const newLogs = [...prev, { time, message: msg }]
      if (newLogs.length > 100) newLogs.shift()
      return newLogs
    })
  }, [])

  const updateStatus = useCallback((status: typeof currentStatus, simulating?: boolean) => {
    setCurrentStatus(status)
    if (simulating !== undefined) setIsSimulating(simulating)
  }, [])

  // Layout Methods
  const toggleMaximize = (target: 'graph' | 'workbench') => {
    setViewMode(viewMode === target ? 'split' : target)
  }

  const handleGoBack = () => {
    navigate(`/ontology/simulation/${currentSimulationId}`)
  }

  const handleNextStep = (reportId?: string) => {
    if (reportId) {
      navigate(`/ontology/report/${reportId}`)
    }
  }

  // Data Logic
  const loadSimulationData = async () => {
    if (!currentSimulationId) return
    try {
      addLog(`Loading simulation: ${currentSimulationId}`)

      const simRes = await simulationApi.get(currentSimulationId)
      if (simRes.data?.success && simRes.data?.data) {
        const simData = simRes.data.data

        if (simData.project_id) {
          const projRes = await graphApi.getProject(simData.project_id)
          if (projRes.data?.success && projRes.data?.data) {
            setProjectData(projRes.data.data)
            addLog(`Project loaded: ${projRes.data.data.project_id}`)

            if (projRes.data.data.graph_id) {
              await loadGraph(projRes.data.data.graph_id)
            }
          }
        }

        // Load simulation config for rounds
        const configRes = await simulationApi.getConfig(currentSimulationId)
        if (configRes.data?.success && configRes.data?.data) {
          if (configRes.data.data.max_rounds) {
            setMaxRounds(configRes.data.data.max_rounds)
          }
        }
      }
    } catch (err: any) {
      addLog(`Sync handshake failed: ${err.message}`)
    } finally {
      dataLoadingRef.current = false
    }
  }

  const loadGraph = async (graphId: string) => {
    setGraphLoading(true)
    try {
      const res = await graphApi.getGraphData(graphId)
      if (res.data?.success) {
        setGraphData(res.data.data)
        addLog('Graph data loaded')
      }
    } catch (err: any) {
      addLog(`Graph load failed: ${err.message}`)
    } finally {
      setGraphLoading(false)
    }
  }

  const refreshGraph = () => {
    if (projectData?.graph_id) {
      loadGraph(projectData.graph_id)
    }
  }

  useEffect(() => {
    addLog('SimulationRunView initialized')
    loadSimulationData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="h-screen flex flex-col bg-[#07080C] text-white/90 overflow-hidden font-sans">
      {/* Header */}
      <header className="h-[60px] border-b border-white/10 flex items-center justify-between px-6 bg-[#07080C]/80 backdrop-blur-md relative z-10">
        <div className="flex items-center">
          <div
            className="font-mono font-extrabold text-lg tracking-wider cursor-pointer text-white"
            onClick={() => navigate('/ontology')}
          >
            aarambh_
          </div>
        </div>

        <div className="absolute left-1/2 transform -translate-x-1/2 transition-all duration-500">
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/10 shadow-2xl backdrop-blur-xl">
            {(['graph', 'split', 'workbench'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`border-none px-5 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all ${viewMode === mode
                  ? 'bg-[var(--accent)] text-[#07080C] shadow-[0_0_20px_rgba(var(--accent-rgb),0.3)]'
                  : 'bg-transparent text-white/40 hover:text-white/80'
                  }`}
              >
                {{ graph: 'Matrix', split: 'Dual', workbench: 'Nodes' }[mode]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="font-mono font-black text-[9px] text-white/20 uppercase tracking-[0.3em]">Module_03</span>
            <span className="font-black text-[10px] uppercase tracking-widest text-[var(--accent)]">Start Simulation</span>
          </div>
          <div className="w-px h-4 bg-white/10" />
          <span className={`flex items-center gap-2 text-[9px] font-black uppercase tracking-widest ${statusClass === 'error' ? 'text-red-400' :
            statusClass === 'completed' ? 'text-emerald-400' :
              isSimulating ? 'text-orange-400' : 'text-white/30'
            }`}>
            <span className={`w-2 h-2 rounded-full shadow-[0_0_10px_currentColor] ${statusClass === 'error' ? 'bg-red-400' :
              statusClass === 'completed' ? 'bg-emerald-400' :
                isSimulating ? 'bg-orange-400 animate-pulse' : 'bg-white/20'
              }`} />
            {statusText}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex relative overflow-hidden">
        {/* Left Panel: Graph */}
        <div
          className="h-full overflow-hidden border-r border-white/10 transition-all duration-300 bg-[#07080C]"
          style={leftPanelStyle}
        >
          <GraphPanel
            graphData={graphData}
            loading={graphLoading}
            currentPhase={3}
            isSimulating={isSimulating}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </div>

        {/* Right Panel: Step3 Simulation */}
        <div
          className="h-full overflow-hidden transition-all duration-300"
          style={rightPanelStyle}
        >
          <Step3Simulation
            simulationId={currentSimulationId}
            maxRounds={maxRounds || 10}
            minutesPerRound={minutesPerRound}
            projectData={projectData}
            graphData={graphData}
            systemLogs={systemLogs}
            onGoBack={handleGoBack}
            onNextStep={handleNextStep}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        </div>
      </main>
    </div>
  )
}

export default OntologySimulationView
