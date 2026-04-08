import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Maximize2, Minimize2, Settings, Activity, Play, Pause, Square,
  ChevronRight, Zap, Database, Globe, MessageSquare, RefreshCcw, BarChart3,
  Clock, Users, TrendingUp, AlertCircle, CheckCircle2
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import GraphPanel from '@/components/ontology/GraphPanel';
import Step3Simulation from '@/components/ontology/Step3Simulation';

// Import APIs
import { graphApi, simulationApi } from '@/api/ontology';

interface SimulationRunViewProps {
  simulationId?: string;
}

export default function SimulationRunView({ simulationId: propSimulationId }: SimulationRunViewProps) {
  const navigate = useNavigate();
  const params = useParams();
  const currentSimulationId = propSimulationId || params.simulationId;

  // Layout State
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('split');
  const [maximizedPanel, setMaximizedPanel] = useState<'graph' | 'workbench' | null>(null);

  // Data State
  const [projectData, setProjectData] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [runStatus, setRunStatus] = useState<any>({});

  // Simulation state
  const [isRunning, setIsRunning] = useState(false);
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(40);
  const [elapsedTime, setElapsedTime] = useState('00:00:00');
  const [actions, setActions] = useState<any[]>([]);

  // Timer for elapsed time
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<Date | null>(null);

  // Initialize data
  useEffect(() => {
    if (currentSimulationId) {
      loadSimulationData();
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [currentSimulationId]);

  // Update elapsed time
  useEffect(() => {
    if (isRunning && startTimeRef.current) {
      timerRef.current = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - startTimeRef.current!.getTime()) / 1000);
        const hours = Math.floor(elapsed / 3600);
        const minutes = Math.floor((elapsed % 3600) / 60);
        const seconds = elapsed % 60;
        setElapsedTime(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRunning]);

  const loadSimulationData = async () => {
    if (!currentSimulationId) return;
    
    setLoading(true);
    try {
      // Load simulation data
      const simRes = await simulationApi.get(currentSimulationId);
      if (simRes.data.success) {
        const simData = simRes.data.data;
        setRunStatus(simData);
        
        // Update running state
        setIsRunning(simData.status === 'running');
        if (simData.status === 'running' && simData.started_at) {
          startTimeRef.current = new Date(simData.started_at);
        }
        
        // Load associated project data
        if (simData.project_id) {
          const projectRes = await graphApi.getProject(simData.project_id);
          if (projectRes.data.success) {
            setProjectData(projectRes.data.data);
          }
        }

        // Load graph data if available
        if (simData.graph_id) {
          loadGraphData(simData.graph_id);
        }

        // Load actions
        loadActions();
      }
    } catch (err) {
      console.error('Failed to load simulation data:', err);
      setError('Failed to load simulation data');
      setCurrentStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const loadGraphData = async (graphId: string) => {
    setGraphLoading(true);
    try {
      const res = await graphApi.getGraphData(graphId);
      if (res.data.success) {
        setGraphData(res.data.data);
      }
    } catch (err) {
      console.error('Failed to load graph data:', err);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadActions = async () => {
    if (!currentSimulationId) return;
    
    try {
      const actionsRes = await simulationApi.getActions(currentSimulationId, 100);
      if (actionsRes.data.success) {
        setActions(actionsRes.data.data.actions || []);
      }
    } catch (err) {
      console.error('Failed to load actions:', err);
    }
  };

  const refreshGraph = useCallback(() => {
    if (graphData?.graph_id || projectData?.graph_id) {
      const graphId = graphData?.graph_id || projectData?.graph_id;
      loadGraphData(graphId);
    }
  }, [graphData?.graph_id, projectData?.graph_id]);

  const toggleMaximize = (panel: 'graph' | 'workbench') => {
    if (maximizedPanel === panel) {
      setMaximizedPanel(null);
    } else {
      setMaximizedPanel(panel);
    }
  };

  const handleStartSimulation = async () => {
    if (!currentSimulationId) return;
    
    try {
      const res = await simulationApi.start({
        simulation_id: currentSimulationId,
        max_rounds: maxRounds
      });
      
      if (res.data.success) {
        setIsRunning(true);
        startTimeRef.current = new Date();
        setCurrentStatus('processing');
        // Poll for updates
        setTimeout(loadSimulationData, 2000);
      }
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError('Failed to start simulation');
    }
  };

  const handleStopSimulation = async () => {
    if (!currentSimulationId) return;
    
    try {
      const res = await simulationApi.stop({
        simulation_id: currentSimulationId
      });
      
      if (res.data.success) {
        setIsRunning(false);
        setCurrentStatus('completed');
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      }
    } catch (err) {
      console.error('Failed to stop simulation:', err);
      setError('Failed to stop simulation');
    }
  };

  const handleNextStep = useCallback((params?: any) => {
    // Navigate to report generation
    if (currentSimulationId) {
      navigate(`/ontology/report/${currentSimulationId}`);
    }
  }, [currentSimulationId, navigate]);

  const handleGoBack = useCallback(() => {
    navigate(`/ontology/simulation/${currentSimulationId}`);
  }, [currentSimulationId, navigate]);

  const addLog = useCallback((msg: string, type: string = 'info') => {
    const timestamp = new Date().toISOString();
    setSystemLogs(prev => [...prev, { timestamp, message: msg, type }]);
  }, []);

  const updateStatus = useCallback((status: any, simulating?: boolean) => {
    setCurrentStatus(status);
    if (simulating !== undefined) {
      setIsRunning(simulating);
    }
  }, []);

  // Computed layout styles
  const leftPanelStyle = useMemo(() => {
    if (maximizedPanel === 'graph' || viewMode === 'graph') {
      return { width: '100%', opacity: 1, transform: 'translateX(0)' };
    }
    if (maximizedPanel === 'workbench' || viewMode === 'workbench') {
      return { width: '0%', opacity: 0, transform: 'translateX(-20px)' };
    }
    return { width: '50%', opacity: 1, transform: 'translateX(0)' };
  }, [viewMode, maximizedPanel]);

  const rightPanelStyle = useMemo(() => {
    if (maximizedPanel === 'graph' || viewMode === 'graph') {
      return { width: '0%', opacity: 0, transform: 'translateX(20px)' };
    }
    if (maximizedPanel === 'workbench' || viewMode === 'workbench') {
      return { width: '100%', opacity: 1, transform: 'translateX(0)' };
    }
    return { width: '50%', opacity: 1, transform: 'translateX(0)' };
  }, [viewMode, maximizedPanel]);

  const statusClass = useMemo(() => {
    switch (currentStatus) {
      case 'processing': return 'status-processing';
      case 'completed': return 'status-completed';
      case 'error': return 'status-error';
      default: return 'status-idle';
    }
  }, [currentStatus]);

  const statusText = useMemo(() => {
    switch (currentStatus) {
      case 'processing': return 'Running Simulation';
      case 'completed': return 'Simulation Complete';
      case 'error': return 'Error';
      default: return 'Ready';
    }
  }, [currentStatus]);

  return (
    <div className="main-view h-screen flex flex-col bg-[#090B10] text-white">
      {/* Header */}
      <header className="app-header h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/50 backdrop-blur-sm">
        <div className="header-left flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="brand text-xl font-black text-white hover:text-white/80 transition-colors cursor-pointer"
          >
            aarambh
          </button>
        </div>
        
        <div className="header-center">
          <div className="view-switcher flex bg-white/5 rounded-xl p-1">
            {(['graph', 'split', 'workbench'] as const).map((mode) => (
              <button
                key={mode}
                className={cn(
                  "switch-btn px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  viewMode === mode 
                    ? "bg-[var(--accent)] text-[#07080C]" 
                    : "text-white/60 hover:text-white hover:bg-white/10"
                )}
                onClick={() => setViewMode(mode)}
              >
                {mode === 'graph' ? 'Graph' : mode === 'split' ? 'Split' : 'Workbench'}
              </button>
            ))}
          </div>
        </div>

        <div className="header-right flex items-center gap-4">
          <div className="workflow-step flex items-center gap-2 text-sm">
            <span className="step-num text-white/60">Step 3/5</span>
            <span className="step-name text-white font-medium">Start Simulation</span>
          </div>
          <div className="step-divider w-px h-4 bg-white/20"></div>
          <span className={cn("status-indicator flex items-center gap-2 text-sm", statusClass)}>
            <span className="dot w-2 h-2 rounded-full bg-current"></span>
            {statusText}
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="content-area flex-1 flex overflow-hidden">
        {/* Left Panel: Graph */}
        <motion.div 
          className="panel-wrapper left border-r border-white/10"
          style={leftPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <GraphPanel 
            graphData={graphData}
            loading={graphLoading}
            currentPhase={3}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </motion.div>

        {/* Right Panel: Step3 Simulation */}
        <motion.div 
          className="panel-wrapper right overflow-hidden"
          style={rightPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <Step3Simulation
            simulationId={currentSimulationId!}
            maxRounds={maxRounds}
            minutesPerRound={60}
            projectData={projectData}
            graphData={graphData}
            systemLogs={systemLogs}
            onNext={handleNextStep}
            onNextStep={handleNextStep}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        </motion.div>
      </main>

      {/* Floating Stats Panel */}
      <AnimatePresence>
        {isRunning && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-6 left-6 bg-black/80 backdrop-blur-md border border-white/10 rounded-2xl p-4 min-w-[300px]"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-400" />
                Live Simulation Stats
              </h4>
              <button
                onClick={handleStopSimulation}
                className="p-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
              >
                <Square className="w-3 h-3" />
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <div className="text-white/60 mb-1">Round</div>
                <div className="text-lg font-bold text-white">{runStatus.current_round || 0}/{maxRounds}</div>
              </div>
              <div>
                <div className="text-white/60 mb-1">Elapsed</div>
                <div className="text-lg font-bold text-white font-mono">{elapsedTime}</div>
              </div>
              <div>
                <div className="text-white/60 mb-1">Actions</div>
                <div className="text-lg font-bold text-white">{actions.length}</div>
              </div>
              <div>
                <div className="text-white/60 mb-1">Status</div>
                <div className="text-lg font-bold text-green-400">Running</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Overlay */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-6 right-6 bg-red-500/20 border border-red-500/50 text-red-300 px-4 py-3 rounded-xl max-w-md"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <p className="text-sm font-medium">Error</p>
                <p className="text-xs opacity-80 mt-1">{error}</p>
              </div>
              <button
                onClick={() => setError('')}
                className="text-red-400 hover:text-red-300"
              >
                ×
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
