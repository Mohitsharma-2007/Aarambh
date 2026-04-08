import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { GraphPanel } from '../components/ontology/GraphPanel'
import { Step5Interaction } from '../components/ontology/Step5Interaction'
import { graphApi, simulationApi, reportApi } from '../api/ontology'

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

export const OntologyInteractionView: React.FC = () => {
  const { reportId: routeReportId } = useParams()
  const navigate = useNavigate()

  // Layout State - default to workbench view
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('workbench')

  // Data State
  const [currentReportId, setCurrentReportId] = useState<string>(routeReportId || '')
  const [simulationId, setSimulationId] = useState<string>('')
  const [projectData, setProjectData] = useState<any>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [systemLogs, setSystemLogs] = useState<LogEntry[]>([])
  const [currentStatus, setCurrentStatus] = useState<'ready' | 'processing' | 'completed' | 'error'>('ready')

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
  const statusText = currentStatus === 'error' ? 'Error' : currentStatus === 'completed' ? 'Completed' : currentStatus === 'processing' ? 'Processing' : 'Ready'

  // Helpers
  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
    setSystemLogs(prev => {
      const newLogs = [...prev, { time, message: msg }]
      if (newLogs.length > 200) newLogs.shift()
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

  // Data Logic
  const loadReportData = async () => {
    if (!currentReportId) return
    try {
      addLog(`Loading report data: ${currentReportId}`)
      
      // Get report info to get simulation_id
      const reportRes = await reportApi.get(currentReportId)
      if (reportRes.data?.success && reportRes.data?.data) {
        const reportData = reportRes.data.data
        if (reportData.simulation_id) {
          setSimulationId(reportData.simulation_id)
          
          // Get simulation info
          const simRes = await simulationApi.get(reportData.simulation_id)
          if (simRes.data?.success && simRes.data?.data) {
            const simData = simRes.data.data
            
            // Get project info
            if (simData.project_id) {
              const projRes = await graphApi.getProject(simData.project_id)
              if (projRes.data?.success && projRes.data?.data) {
                setProjectData(projRes.data.data)
                addLog(`Project loaded: ${projRes.data.data.project_id}`)
                
                // Get graph data
                if (projRes.data.data.graph_id) {
                  await loadGraph(projRes.data.data.graph_id)
                }
              }
            }
          }
        }
      } else {
        addLog(`Failed to get report info: ${reportRes.data?.error || 'Unknown error'}`)
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
    if (routeReportId && routeReportId !== currentReportId) {
      setCurrentReportId(routeReportId)
      loadReportData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeReportId])

  useEffect(() => {
    addLog('InteractionView initialized')
    if (currentReportId) {
      loadReportData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden font-sans">
      {/* Header */}
      <header className="h-[60px] border-b border-gray-200 flex items-center justify-between px-6 bg-white relative z-10">
        <div className="flex items-center">
          <div 
            className="font-mono font-extrabold text-lg tracking-wider cursor-pointer"
            onClick={() => navigate('/ontology')}
          >
            aarambh
          </div>
        </div>
        
        <div className="absolute left-1/2 transform -translate-x-1/2">
          <div className="flex bg-gray-100 p-1 rounded-md gap-1">
            {(['graph', 'split', 'workbench'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`border-none px-4 py-1.5 text-xs font-semibold rounded transition-all ${
                  viewMode === mode
                    ? 'bg-white text-black shadow-sm'
                    : 'bg-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {{ graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-mono font-bold text-gray-400">Step 5/5</span>
            <span className="font-bold text-black">Deep Interaction</span>
          </div>
          <div className="w-px h-3.5 bg-gray-300" />
          <span className={`flex items-center gap-2 text-xs font-medium ${
            statusClass === 'error' ? 'text-red-500' :
            statusClass === 'completed' ? 'text-green-500' :
            statusClass === 'processing' ? 'text-orange-500' : 'text-gray-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              statusClass === 'error' ? 'bg-red-500' :
              statusClass === 'completed' ? 'bg-green-500' :
              statusClass === 'processing' ? 'bg-orange-500 animate-pulse' : 'bg-gray-400'
            }`} />
            {statusText}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex relative overflow-hidden">
        {/* Left Panel: Graph */}
        <div 
          className="h-full overflow-hidden border-r border-gray-200 transition-all duration-300"
          style={leftPanelStyle}
        >
          <GraphPanel
            graphData={graphData}
            loading={graphLoading}
            currentPhase={5}
            isSimulating={false}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </div>

        {/* Right Panel: Step5 Deep Interaction */}
        <div 
          className="h-full overflow-hidden transition-all duration-300"
          style={rightPanelStyle}
        >
          <Step5Interaction
            reportId={currentReportId}
            simulationId={simulationId}
            systemLogs={systemLogs}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        </div>
      </main>
    </div>
  )
}

export default OntologyInteractionView
