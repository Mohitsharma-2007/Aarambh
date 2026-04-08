import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Maximize2, Minimize2, Settings, Activity,
  ChevronRight, Zap, Database, Globe, MessageSquare, FileText,
  Download, Share2, Eye, BarChart3, TrendingUp, Clock, Users, CheckCircle
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Import components
import GraphPanel from '@/components/ontology/GraphPanel';
import Step4Report from '@/components/ontology/Step4Report';

// Import APIs
import { graphApi, simulationApi, reportApi } from '@/api/ontology';

interface ReportViewProps {
  simulationId?: string;
}

export default function ReportView({ simulationId: propSimulationId }: ReportViewProps) {
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
  const [reportData, setReportData] = useState<any>(null);
  const [reportStatus, setReportStatus] = useState<any>(null);

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

        // Check for existing report
        await loadReportData();
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

  const loadReportData = async () => {
    if (!currentSimulationId) return;
    
    try {
      // Try to get existing report
      const reportRes = await reportApi.getStatus();
      if (reportRes.data.success && reportRes.data.data) {
        setReportData(reportRes.data.data);
        setReportStatus('loaded');
        setCurrentStatus('completed');
      } else {
        // Generate new report
        await generateReport();
      }
    } catch (err) {
      console.error('Failed to load report data:', err);
      // Try to generate new report
      await generateReport();
    }
  };

  const generateReport = async () => {
    if (!currentSimulationId || !projectData) return;
    
    setReportStatus('generating');
    setCurrentStatus('processing');
    
    try {
      const res = await reportApi.generate({
        simulation_id: currentSimulationId,
        project_id: projectData.project_id,
        graph_id: projectData.graph_id
      });
      
      if (res.data.success) {
        // Poll for report completion
        pollReportStatus(res.data.data.task_id);
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
      setError('Failed to generate report');
      setCurrentStatus('error');
      setReportStatus('error');
    }
  };

  const pollReportStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await reportApi.getStatus({ task_id: taskId });
        if (statusRes.data.success) {
          const status = statusRes.data.data;
          
          if (status.status === 'completed') {
            clearInterval(pollInterval);
            // Load the completed report
            const reportRes = await reportApi.get(status.report_id);
            if (reportRes.data.success) {
              setReportData(reportRes.data.data);
              setReportStatus('completed');
              setCurrentStatus('completed');
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setError('Report generation failed');
            setCurrentStatus('error');
            setReportStatus('error');
          }
        }
      } catch (err) {
        console.error('Error polling report status:', err);
      }
    }, 3000);
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
    // Navigate to interaction view
    if (currentSimulationId) {
      navigate(`/ontology/interaction/${currentSimulationId}`);
    }
  }, [currentSimulationId, navigate]);

  const handleGoBack = useCallback(() => {
    navigate(`/ontology/simulation-run/${currentSimulationId}`);
  }, [currentSimulationId, navigate]);

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
      case 'processing': return 'Generating Report...';
      case 'completed': return 'Report Ready';
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
            <span className="step-num text-white/60">Step 4/5</span>
            <span className="step-name text-white font-medium">Report Generation</span>
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
            currentPhase={4}
            onRefresh={refreshGraph}
            onToggleMaximize={() => toggleMaximize('graph')}
          />
        </motion.div>

        {/* Right Panel: Step4 Report */}
        <motion.div 
          className="panel-wrapper right overflow-hidden"
          style={rightPanelStyle}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <Step4Report
            reportId={reportData?.report_id || ''}
            simulationId={currentSimulationId!}
            onNext={handleNextStep}
          />
        </motion.div>
      </main>

      {/* Report Generation Progress */}
      <AnimatePresence>
        {reportStatus === 'generating' && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-6 left-6 bg-black/80 backdrop-blur-md border border-white/10 rounded-2xl p-4 min-w-[300px]"
          >
            <div className="flex items-center gap-3">
              <div className="animate-spin">
                <Settings className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h4 className="text-sm font-medium text-white">Generating Report</h4>
                <p className="text-xs text-white/60 mt-1">Analyzing simulation data and creating insights...</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Report Ready Notification */}
      <AnimatePresence>
        {reportStatus === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-6 left-6 bg-green-500/20 backdrop-blur-md border border-green-500/50 rounded-2xl p-4 min-w-[300px]"
          >
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <div>
                <h4 className="text-sm font-medium text-white">Report Ready</h4>
                <p className="text-xs text-white/60 mt-1">Your simulation report has been generated successfully.</p>
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
