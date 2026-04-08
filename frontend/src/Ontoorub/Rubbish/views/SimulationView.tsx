import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Maximize2, Minimize2, Settings, Activity,
  ChevronRight, Zap, Database, Globe, MessageSquare, Play, Square
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import GraphPanel from '@/components/ontology/GraphPanel';
import Step2EnvSetup from '@/components/ontology/Step2EnvSetup';

// Import APIs
import { graphApi, simulationApi } from '@/api/ontology';

interface SimulationViewProps {
  simulationId?: string;
}

export default function SimulationView({ simulationId: propSimulationId }: SimulationViewProps) {
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
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('processing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Initialize data
  useEffect(() => {
    if (currentSimulationId) {
      loadSimulationData();
    }
  }, [currentSimulationId]);

  const loadSimulationData = async () => {
    if (!currentSimulationId) return;
    
    setLoading(true);
    try {
      // Load simulation data
      const simRes = await simulationApi.get(currentSimulationId);
      if (simRes.data.success) {
        const simData = simRes.data.data;
        
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

  const handleNextStep = useCallback((params?: any) => {
    // Navigate to next step or simulation run view
    if (currentSimulationId) {
      navigate(`/ontology/simulation-run/${currentSimulationId}`);
    }
  }, [currentSimulationId, navigate]);

  const handleGoBack = useCallback(() => {
    navigate('/ontology/main/' + (projectData?.project_id || 'new'));
  }, [projectData?.project_id, navigate]);

  const addLog = useCallback((msg: string, type: string = 'info') => {
    const timestamp = new Date().toISOString();
    setSystemLogs(prev => [...prev, { timestamp, message: msg, type }]);
  }, []);

  const updateStatus = useCallback((status: any, simulating?: boolean) => {
    setCurrentStatus(status);
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
      case 'processing': return 'Processing...';
      case 'completed': return 'Completed';
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
            <span className="step-num text-white/60">Step 2/5</span>
            <span className="step-name text-white font-medium">Environment Setup</span>
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
            currentPhase={2}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </motion.div>

        {/* Right Panel: Step2 Environment Setup */}
        <motion.div 
          className="panel-wrapper right overflow-hidden"
          style={rightPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <Step2EnvSetup
            simulationId={currentSimulationId}
            projectData={projectData}
            graphData={graphData}
            systemLogs={systemLogs}
            onGoBack={handleGoBack}
            onNext={handleNextStep}
            onNextStep={handleNextStep}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        </motion.div>
      </main>

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
