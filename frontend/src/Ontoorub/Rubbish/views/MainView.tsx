import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Maximize2, Minimize2, Settings, Activity,
  ChevronRight, Zap, Database, Globe, MessageSquare
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import GraphPanel from '@/components/ontology/GraphPanel';
import Step1GraphBuild from '@/components/ontology/Step1GraphBuild';
import Step2EnvSetup from '@/components/ontology/Step2EnvSetup';
import Step3Simulation from '@/components/ontology/Step3Simulation';
import Step4Report from '@/components/ontology/Step4Report';
import Step5Interaction from '@/components/ontology/Step5Interaction';

// Import APIs
import { graphApi } from '@/api/ontology';

interface MainViewProps {
  projectId?: string;
}

export default function MainView({ projectId }: MainViewProps) {
  const navigate = useNavigate();
  const params = useParams();
  const currentProjectId = projectId || params.projectId;

  // Layout State
  const [viewMode, setViewMode] = useState<'graph' | 'split' | 'workbench'>('split');
  const [maximizedPanel, setMaximizedPanel] = useState<'graph' | 'workbench' | null>(null);

  // Step State
  const [currentStep, setCurrentStep] = useState(1);
  const stepNames = [
    'Knowledge Graph Construction',
    'Environment Setup', 
    'Start Simulation',
    'Report Generation',
    'Deep Interaction'
  ];

  // Data State
  const [projectData, setProjectData] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);
  const [error, setError] = useState('');
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [currentStatus, setCurrentStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');

  // Progress State
  const [ontologyProgress, setOntologyProgress] = useState(0);
  const [buildProgress, setBuildProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState(0);

  // Initialize project data
  useEffect(() => {
    if (currentProjectId && currentProjectId !== 'new') {
      loadProjectData();
    }
  }, [currentProjectId]);

  const loadProjectData = async () => {
    if (!currentProjectId || currentProjectId === 'new') return;
    
    setLoading(true);
    try {
      // Load project data
      const projectRes = await graphApi.getProject(currentProjectId);
      if (projectRes.data.success) {
        setProjectData(projectRes.data.data);
      }

      // Load graph data if available
      if (projectData?.graph_id) {
        loadGraphData(projectData.graph_id);
      }
    } catch (err) {
      console.error('Failed to load project data:', err);
      setError('Failed to load project data');
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
    if (projectData?.graph_id) {
      loadGraphData(projectData.graph_id);
    }
  }, [projectData?.graph_id]);

  const toggleMaximize = (panel: 'graph' | 'workbench') => {
    if (maximizedPanel === panel) {
      setMaximizedPanel(null);
    } else {
      setMaximizedPanel(panel);
    }
  };

  const handleNextStep = (params?: any) => {
    if (currentStep < 5) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleGoBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

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

  const renderStepComponent = () => {
    const commonProps = {
      projectData,
      graphData,
      systemLogs,
      onAddLog: addLog,
      onUpdateStatus: updateStatus,
      onNext: handleNextStep,
      onNextStep: handleNextStep,
      onGoBack: handleGoBack,
      onBack: handleGoBack
    };

    switch (currentStep) {
      case 1:
        return (
          <Step1GraphBuild
            currentPhase={currentPhase}
            projectData={projectData}
            ontologyProgress={ontologyProgress}
            buildProgress={buildProgress}
            graphData={graphData}
            systemLogs={systemLogs}
            onNext={handleNextStep}
            addLog={addLog}
          />
        );
      case 2:
        return <Step2EnvSetup {...commonProps} />;
      case 3:
        return (
          <Step3Simulation
            simulationId={projectData?.simulation_id}
            maxRounds={40}
            minutesPerRound={60}
            projectData={projectData}
            graphData={graphData}
            systemLogs={systemLogs}
            onNext={handleNextStep}
            onAddLog={addLog}
            onUpdateStatus={updateStatus}
          />
        );
      case 4:
        return (
          <Step4Report
            simulationId={projectData?.simulation_id}
            projectData={projectData}
            graphData={graphData}
            onNext={handleNextStep}
            onAddLog={addLog}
          />
        );
      case 5:
        return (
          <Step5Interaction
            simulationId={projectData?.simulation_id}
            projectData={projectData}
            graphData={graphData}
            onAddLog={addLog}
          />
        );
      default:
        return null;
    }
  };

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
            <span className="step-num text-white/60">Step {currentStep}/5</span>
            <span className="step-name text-white font-medium">{stepNames[currentStep - 1]}</span>
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
            currentPhase={currentPhase}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </motion.div>

        {/* Right Panel: Step Components */}
        <motion.div 
          className="panel-wrapper right overflow-hidden"
          style={rightPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          {renderStepComponent()}
        </motion.div>
      </main>
    </div>
  );
}
