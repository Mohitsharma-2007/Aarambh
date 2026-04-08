import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Database, Layout, Maximize2, Minimize2, 
  ChevronRight, Activity, Terminal, Shield, Cpu
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { graphApi } from '@/api/ontology';
import GraphPanel from '@/components/ontology/GraphPanel';
import Step1GraphBuild from '@/components/ontology/Step1GraphBuild';
import Step2EnvSetup from '@/components/ontology/Step2EnvSetup';
import Step3Simulation from '@/components/ontology/Step3Simulation';
import Step4Report from '@/components/ontology/Step4Report';
import Step5Interaction from '@/components/ontology/Step5Interaction';

type ViewMode = 'graph' | 'split' | 'workbench';

const STEP_NAMES = [
  'Graph Construction',
  'Environment Setup',
  'Simulation Phase',
  'Analytical Synthesis',
  'Deep Interaction'
];

export default function OntologyMain() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  // Layout State
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  const [currentStep, setCurrentStep] = useState(1);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [maxRounds, setMaxRounds] = useState<number | undefined>(undefined);
  const [reportId, setReportId] = useState<string | null>(null);
  
  // Data State
  const [projectData, setProjectData] = useState<any>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(-1); // -1: Init, 0: Ontology, 1: Build, 2: Ready
  const [ontologyProgress, setOntologyProgress] = useState<any>(null);
  const [buildProgress, setBuildProgress] = useState<any>(null);
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [error, setError] = useState('');

  // Polling logic
  useEffect(() => {
    if (projectId && projectId !== 'new') {
      loadProject();
    }
  }, [projectId]);

  const addLog = useCallback((msg: string, type = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setSystemLogs(prev => [{ time, msg, type }, ...prev].slice(0, 100));
  }, []);

  const loadProject = async () => {
    if (!projectId) return;
    try {
      addLog(`Connecting to project cluster: ${projectId.slice(0, 8)}...`);
      const res = await graphApi.getProject(projectId);
      if (res.data.success) {
        setProjectData(res.data.data);
        updatePhaseByStatus(res.data.data.status);
        if (res.data.data.graph_id) {
          loadGraph(res.data.data.graph_id);
        }
      }
    } catch (err: any) {
      setError(err.message);
      addLog(`Handshake failed: ${err.message}`, 'error');
    }
  };

  const updatePhaseByStatus = (status: string) => {
    switch (status) {
      case 'ontology_generated': setCurrentPhase(0); break;
      case 'graph_building': setCurrentPhase(1); break;
      case 'graph_completed': setCurrentPhase(2); break;
      default: setCurrentPhase(-1);
    }
  };

  const loadGraph = async (graphId: string) => {
    setGraphLoading(true);
    try {
      const res = await graphApi.getGraphData(graphId);
      if (res.data.success) {
        setGraphData(res.data.data);
        addLog(`Neural matrix synchronized. Clusters verified.`);
      }
    } catch (err) {
      addLog(`Sync error in graph segment`, 'error');
    } finally {
      setGraphLoading(false);
    }
  };

  const handleNextStep = () => {
    if (currentStep < 5) setCurrentStep(v => v + 1);
  };

  return (
    <div className="h-screen bg-[#07080C] text-white flex flex-col overflow-hidden selection:bg-[var(--accent)]/30">
      {/* Dynamic Header */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#090B10]/80 backdrop-blur-xl z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/ontology')}>
            <div className="p-2 bg-[var(--accent)]/10 rounded-lg text-[var(--accent)] group-hover:scale-110 transition-transform">
              <Database className="w-5 h-5" />
            </div>
            <span className="text-lg font-black tracking-tighter uppercase italic">AARAMBH</span>
          </div>
          <div className="h-4 w-px bg-white/10 hidden md:block" />
          <div className="flex items-center gap-4 hidden lg:flex">
            <span className="text-[9px] font-black bg-white/5 border border-white/10 px-2 py-1 rounded uppercase tracking-widest text-white/40">Step 0{currentStep} / 05</span>
            <span className="text-xs font-black uppercase tracking-[0.2em] text-[var(--accent)]">{STEP_NAMES[currentStep-1]}</span>
          </div>
        </div>

        <div className="flex items-center gap-8">
          {/* View Switcher */}
          <div className="flex items-center bg-black/40 border border-white/5 p-1 rounded-xl">
            {(['graph', 'split', 'workbench'] as ViewMode[]).map(m => (
              <button 
                key={m}
                onClick={() => setViewMode(m)}
                className={cn(
                  "px-4 py-2 text-[9px] font-black uppercase tracking-widest rounded-lg transition-all",
                  viewMode === m ? "bg-[var(--accent)] text-[#07080C]" : "text-white/30 hover:text-white"
                )}
              >
                {m}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full border text-[9px] font-black uppercase tracking-widest",
              currentPhase >= 2 ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400" : "border-orange-500/20 bg-orange-500/5 text-orange-400"
            )}>
              <span className={cn("w-1.5 h-1.5 rounded-full", currentPhase >= 2 ? "bg-emerald-400" : "bg-orange-400 animate-pulse")} />
              {currentPhase >= 2 ? "Sync Ready" : currentPhase === 1 ? "Mapping Nodes" : "Initializing"}
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left: Graph Panel */}
        <AnimatePresence>
          {viewMode !== 'workbench' && (
            <motion.div 
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: viewMode === 'graph' ? '100%' : '50%', opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="border-r border-white/5 overflow-hidden h-full relative"
            >
              <div className="absolute top-4 right-4 z-20">
                <button onClick={() => setViewMode(viewMode === 'graph' ? 'split' : 'graph')} className="p-2 bg-black/40 border border-white/10 rounded-lg text-white/40 hover:text-white hover:border-white/20 transition-all">
                  {viewMode === 'graph' ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
              </div>
              <GraphPanel 
                graphData={graphData} 
                loading={graphLoading} 
                currentPhase={currentPhase}
                onRefresh={() => projectId && loadGraph(projectId)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Right: Steps Workbench */}
        <AnimatePresence>
          {viewMode !== 'graph' && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: viewMode === 'workbench' ? '100%' : '50%', opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="h-full flex flex-col bg-[#07080C]"
            >
              <div className="flex-1 overflow-y-auto scrollable p-8 space-y-8">
                {currentStep === 1 && (
                  <Step1GraphBuild 
                    currentPhase={currentPhase}
                    projectData={projectData}
                    graphData={graphData}
                    buildProgress={buildProgress}
                    onNext={handleNextStep}
                    addLog={addLog}
                  />
                )}
                {currentStep === 2 && (
                  <Step2EnvSetup 
                    projectData={projectData}
                    graphData={graphData}
                    onBack={() => setCurrentStep(1)}
                    onNext={(params) => {
                      if (params?.maxRounds) setMaxRounds(params.maxRounds);
                      setCurrentStep(3);
                    }}
                  />
                )}
                {currentStep === 3 && projectId && (
                  <Step3Simulation 
                    simulationId={simulationId || ''}
                    maxRounds={maxRounds}
                    projectData={projectData}
                    onNext={(params) => {
                      if (params?.reportId) setReportId(params.reportId);
                      setCurrentStep(4);
                    }}
                  />
                )}
                {currentStep === 4 && reportId && (
                  <Step4Report 
                    reportId={reportId}
                    simulationId={simulationId || ''}
                    onNext={() => setCurrentStep(5)}
                  />
                )}
                {currentStep === 5 && reportId && (
                  <Step5Interaction 
                    reportId={reportId}
                    simulationId={simulationId || ''}
                  />
                )}
              </div>

              {/* Console Bar */}
              <div className="h-48 border-t border-white/5 bg-[#090B10] p-6 font-mono text-[10px] flex flex-col">
                <div className="flex justify-between items-center mb-4 text-white/20 uppercase tracking-widest font-black">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-[var(--accent)]" />
                    <span>System Protocol Console</span>
                  </div>
                  <span>Kernel v1.0.OA</span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 text-white/40 custom-scrollbar">
                  {systemLogs.length === 0 ? (
                    <div className="italic text-white/5 uppercase tracking-tighter">Waiting for sequence trigger...</div>
                  ) : (
                    systemLogs.map((l, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="text-white/10 shrink-0">[{l.time}]</span>
                        <span className={cn(
                          l.type === 'error' ? 'text-red-500' :
                          l.type === 'success' ? 'text-emerald-500' : 
                          'text-white/60'
                        )}>{l.msg}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
