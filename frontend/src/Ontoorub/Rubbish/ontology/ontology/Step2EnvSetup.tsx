import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu, Users, Settings, Zap, Play, ChevronLeft,
  ChevronRight, Info, X, Terminal, Globe, MessageSquare
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { simulationApi } from '@/api/ontology';

interface Step2EnvSetupProps {
  simulationId?: string;
  projectData: any;
  graphData: any;
  systemLogs?: any[];
  onBack?: () => void;
  onGoBack?: () => void;
  onNext?: (params?: any) => void;
  onNextStep?: (params?: any) => void;
  onAddLog?: (msg: string) => void;
  onUpdateStatus?: (status: any) => void;
}

export default function Step2EnvSetup({
  simulationId,
  projectData,
  graphData,
  systemLogs,
  onBack,
  onGoBack,
  onNext,
  onNextStep,
  onAddLog,
  onUpdateStatus
}: Step2EnvSetupProps) {
  const [phase, setPhase] = useState(0); // 0-4 matching Vue
  const [activeSimId, setActiveSimId] = useState<string | null>(simulationId || null);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [simulationConfig, setSimulationConfig] = useState<any>(null);
  const [selectedProfile, setSelectedProfile] = useState<any>(null);
  const [useCustomRounds, setUseCustomRounds] = useState(false);
  const [customMaxRounds, setCustomMaxRounds] = useState(40);
  const [loading, setLoading] = useState(false);
  const loadingDataRef = useRef(false);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const taskIdRef = useRef<string | null>(null);

  // Auto-init simulation on mount if no ID provided
  useEffect(() => {
    if (!activeSimId && projectData?.project_id) {
      initSimulation();
    } else if (activeSimId && !profiles.length && !loadingDataRef.current) {
      // If we have an ID but no profiles, check if it's ready then load
      loadSimulationData(activeSimId);
    }
  }, [projectData?.project_id, activeSimId]);

  const initSimulation = async () => {
    setLoading(true);
    try {
      const res = await simulationApi.create({
        project_id: projectData.project_id,
        graph_id: projectData.graph_id,
        enable_twitter: true,
        enable_reddit: true
      });
      if (res.data.success) {
        const newId = res.data.data.simulation_id;
        setActiveSimId(newId);
        // Start prepare automatically
        startPrepare(newId);
      }
    } catch (err) {
      console.error(err);
      onAddLog?.(`Init Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const loadSimulationData = async (sid: string) => {
    if (!sid || loadingDataRef.current) return;
    loadingDataRef.current = true;
    try {
      // 1. Check if simulation even exists/is prepared
      const simRes = await simulationApi.get(sid);
      const simData = simRes.data.data;

      // If it exists but not prepared, don't try to load config yet
      if (!simData || (simData.status !== 'ready' && simData.status !== 'running' && phase < 4)) {
        console.debug('Simulation not prepared according to API', sid);

        // Auto-start prepare if we're at the beginning and it's just created
        if (phase === 0 && simData?.status === 'created') {
          startPrepare(sid);
        } else if (simData?.status === 'preparing') {
          // If already preparing, ensure we are polling
          if (phase < 1) setPhase(1);
          startPolling(sid);
        }

        loadingDataRef.current = false;
        return;
      }

      // If it is ready, ensure we are at phase 4
      if (simData.status === 'ready' || simData.status === 'running') {
        setPhase(4);
        onUpdateStatus?.('completed');
      }

      // 2. Load profiles
      const res = await simulationApi.getProfiles(sid);
      if (res.data.success) {
        setProfiles(res.data.data || []);
      }

      // 3. Load config
      const configRes = await simulationApi.getConfig(sid);
      if (configRes.data.success) {
        setSimulationConfig(configRes.data.data);
      }
    } catch (err) {
      // Silently handle if resource not ready yet
      console.debug('Simulation resource pending for', sid);
    } finally {
      loadingDataRef.current = false;
    }
  };

  const startPrepare = async (sid: string) => {
    setPhase(1);
    onUpdateStatus?.('processing');
    try {
      const res = await simulationApi.prepare({
        simulation_id: sid,
      });
      if (res.data?.success && res.data.data?.task_id) {
        taskIdRef.current = res.data.data.task_id;
        onAddLog?.('Preparing neural simulation workspace...');
        startPolling(sid);
      } else if (res.data?.success && res.data.data?.already_prepared) {
        setPhase(4);
        loadSimulationData(sid);
        onUpdateStatus?.('completed');
      }
    } catch (err) {
      console.error(err);
      onUpdateStatus?.('error');
    }
  };

  const startPolling = (sid: string) => {
    if (pollTimerRef.current) return;

    const runPoll = async () => {
      try {
        const res = await simulationApi.getPrepareStatus({
          simulation_id: sid,
          task_id: taskIdRef.current || undefined
        });

        if (res.data?.success) {
          const data = res.data.data;

          if (data.status === 'ready' || data.status === 'completed') {
            onAddLog?.('Execution buffer ready.');
            setPhase(4);
            loadSimulationData(sid);
            onUpdateStatus?.('completed');
            stopPolling();
            return;
          }

          if (data.status === 'processing') {
            const detail = data.progress_detail;
            if (detail?.current_stage) {
              // Map stages to phases
              // reading: 1, generating_profiles: 2, generating_config: 3
              if (detail.current_stage === 'reading') setPhase(1);
              else if (detail.current_stage === 'generating_profiles') setPhase(2);
              else if (detail.current_stage === 'generating_config') setPhase(3);
              else if (detail.current_stage === 'copying_scripts') setPhase(4);
            }
          }

          if (data.status === 'failed') {
            onUpdateStatus?.('error');
            onAddLog?.(`Preparation failed: ${data.error || 'Unknown error'}`);
            stopPolling();
          }
        }
      } catch (err) {
        console.warn('Poll failed', err);
      }
    };

    runPoll();
    pollTimerRef.current = setInterval(runPoll, 3000);
  };

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const loadMockProfiles = () => {
    setProfiles([
      { name: 'Alpha', username: 'Analyst_01', profession: 'Market Strategist', bio: 'Specializes in high-frequency sentiment analysis.', stance: 'NEUTRAL' },
      { name: 'Beta', username: 'Trader_X', profession: 'Crypto Whale', bio: 'Opportunistic mover in volatile markets.', stance: 'BULLISH' },
      { name: 'Gamma', username: 'Skeptic_99', profession: 'Economic Critic', bio: 'Systematic analyzer of structural weaknesses.', stance: 'BEARISH' },
    ]);
  };

  const autoGeneratedRounds = useMemo(() => {
    if (!simulationConfig?.time_config) return 40;
    const { total_simulation_hours: h, minutes_per_round: m } = simulationConfig.time_config;
    return Math.max(Math.floor((h * 60) / m), 40);
  }, [simulationConfig]);

  const handleNext = (params: any) => {
    if (onNextStep) onNextStep(params);
    else if (onNext) onNext(params);
  };

  const handleBack = () => {
    if (onGoBack) onGoBack();
    else if (onBack) onBack();
  };

  return (
    <div className="space-y-6 relative pb-20">
      {/* Profile Detail Modal */}
      <AnimatePresence>
        {selectedProfile && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md"
            onClick={() => setSelectedProfile(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }}
              className="w-full max-w-2xl bg-[#090B10] border border-white/10 rounded-3xl overflow-hidden shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <div className="p-8 border-b border-white/5 flex justify-between items-start bg-white/[0.02]">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-black text-white uppercase">{selectedProfile.username}</h3>
                    <span className="text-[10px] font-black text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-1 rounded truncate">@{selectedProfile.name}</span>
                  </div>
                  <p className="text-xs font-bold text-white/40 uppercase tracking-widest">{selectedProfile.profession}</p>
                </div>
                <button onClick={() => setSelectedProfile(null)} className="p-2 hover:bg-white/5 rounded-xl transition-all"><X /></button>
              </div>
              <div className="p-8 space-y-8 uppercase tracking-tight">
                <div className="space-y-3">
                  <h5 className="text-[10px] font-black text-white/20 tracking-[0.2em]">Causal Profile Bio</h5>
                  <p className="text-sm text-white/60 leading-relaxed italic border-l-2 border-[var(--accent)] pl-6">"{selectedProfile.bio}"</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center justify-between mb-8">
        <button onClick={handleBack} className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/40 hover:text-white transition-all">
          <ChevronLeft className="w-4 h-4" /> Return to Graph Construction
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Phase 01: Simulation Initialization */}
        <PhaseCard num="01" title="Simulation Hub Setup" status={phase > 0 ? 'completed' : 'active'} isActive={phase === 0}>
          <div className="space-y-4">
            <p className="text-xs text-white/40 leading-relaxed italic uppercase">Allocating neural workspace & bootstrapping simulation kernels.</p>
            {activeSimId && (
              <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-[8px] font-black text-white/10 uppercase tracking-widest">Simulation ID</span>
                  <p className="text-[10px] font-mono text-[var(--accent)] truncate">{activeSimId}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[8px] font-black text-white/10 uppercase tracking-widest">Kernel Status</span>
                  <p className="text-[10px] font-mono text-emerald-400">ACTIVE_LNX</p>
                </div>
              </div>
            )}
          </div>
        </PhaseCard>

        {/* Phase 02: Agent Profiling */}
        <PhaseCard num="02" title="Neural Agent Profiling" status={phase > 1 ? 'completed' : phase === 1 ? 'active' : 'pending'} isActive={phase === 1}>
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed italic uppercase">Extracting actor entities from matrix & injecting reality seeds.</p>
            {profiles.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {profiles.map((p, i) => (
                  <motion.div
                    key={i}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => setSelectedProfile(p)}
                    className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-[var(--accent)]/30 cursor-pointer transition-all group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[10px] font-black text-white/80 group-hover:text-[var(--accent)] transition-colors">{p.username}</span>
                      <div className={cn("w-1.5 h-1.5 rounded-full", p.stance === 'BULLISH' ? 'bg-emerald-400' : p.stance === 'BEARISH' ? 'bg-red-400' : 'bg-white/20')} />
                    </div>
                    <p className="text-[9px] text-white/20 truncate uppercase tracking-tighter">{p.profession}</p>
                  </motion.div>
                ))}
              </div>
            )}
            {phase === 1 && (
              <div className="flex items-center gap-3 p-4 rounded-2xl bg-[var(--accent)]/5 border border-[var(--accent)]/20 animate-pulse">
                <Users className="w-4 h-4 text-[var(--accent)]" />
                <span className="text-[10px] font-black text-[var(--accent)] tracking-widest uppercase">Synthesizing Digital Personas...</span>
              </div>
            )}
          </div>
        </PhaseCard>

        {/* Phase 03: Platform Config */}
        <PhaseCard num="03" title="Algorithm Parameterization" status={phase > 2 ? 'completed' : phase === 2 ? 'active' : 'pending'} isActive={phase === 2}>
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed italic uppercase">Configuring multi-platform reach & engagement echo-chambers.</p>
            <div className="grid grid-cols-2 gap-4">
              <PlatformMiniCard name="Twitter/X" status="SYNCED" color="blue" />
              <PlatformMiniCard name="Reddit" status="SYNCED" color="orange" />
            </div>
          </div>
        </PhaseCard>

        {/* Phase 04: Sequence Readiness */}
        <PhaseCard num="05" title="Execution Buffer Ready" status={phase >= 4 ? 'active' : 'pending'} isActive={phase === 4}>
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed italic uppercase">Recursive simulation parameters locked. Integrity: 99.8%. Ready for sequence launch.</p>

            <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/5 space-y-6">
              <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-[0.2em]">
                <span className="text-white/30 italic">Target Iterations</span>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={useCustomRounds} onChange={e => setUseCustomRounds(e.target.checked)} className="w-3 h-3 accent-[var(--accent)]" />
                    <span className="text-white/20">CUSTOM_LIMIT</span>
                  </label>
                  <span className="text-[var(--accent)]">{useCustomRounds ? customMaxRounds : autoGeneratedRounds} SEGS</span>
                </div>
              </div>

              {useCustomRounds && (
                <input
                  type="range" min="10" max={autoGeneratedRounds} step="5"
                  value={customMaxRounds} onChange={e => setCustomMaxRounds(parseInt(e.target.value))}
                  className="w-full h-1 bg-white/10 rounded-full appearance-none accent-[var(--accent)]"
                />
              )}
            </div>

            <button
              onClick={() => handleNext({ maxRounds: useCustomRounds ? customMaxRounds : autoGeneratedRounds })}
              disabled={phase < 4}
              className={cn(
                "w-full h-16 rounded-3xl flex items-center justify-center gap-4 transition-all font-black uppercase tracking-[0.5em] text-xs",
                phase >= 4
                  ? "bg-[var(--accent)] text-[#07080C] shadow-[0_0_50px_rgba(var(--accent-rgb),0.3)] hover:scale-[1.02] active:scale-[0.98]"
                  : "bg-white/5 text-white/10 border border-white/5 cursor-not-allowed italic"
              )}
            >
              <Play className="w-5 h-5 fill-current" /> Execute Parrelel Simulation
            </button>
          </div>
        </PhaseCard>
      </div>
    </div>
  );
}

function PhaseCard({ num, title, status, isActive, children }: any) {
  const isCompleted = status === 'completed';
  const isPending = status === 'pending';

  return (
    <motion.div
      animate={{ opacity: isPending ? 0.3 : 1 }}
      className={cn(
        "glass-card !bg-[#090B10]/40 border-white/5 transition-all duration-500",
        isActive && "border-[var(--accent)]/30 !bg-[var(--accent)]/[0.01] shadow-[0_0_50px_rgba(var(--accent-rgb),0.03)]",
        isCompleted && "border-emerald-500/10"
      )}
    >
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <div className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm",
            isActive ? "bg-[var(--accent)] text-[#07080C]" :
              isCompleted ? "bg-emerald-500/10 text-emerald-400" : "bg-white/5 text-white/10"
          )}>
            {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : num}
          </div>
          <h4 className={cn("text-[10px] font-black uppercase tracking-[0.2em]", isActive ? "text-white" : "text-white/30")}>{title}</h4>
        </div>
        <span className={cn(
          "text-[8px] font-black uppercase tracking-widest px-2 py-1 rounded border",
          isActive ? "border-[var(--accent)]/20 text-[var(--accent)]" : "border-white/5 text-white/10"
        )}>{status}</span>
      </div>
      {children}
    </motion.div>
  );
}

function PlatformMiniCard({ name, status, color }: any) {
  return (
    <div className="p-4 rounded-2xl bg-white/[0.01] border border-white/5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Globe className={cn("w-4 h-4", color === 'blue' ? 'text-blue-400' : 'text-orange-400')} />
        <span className="text-[10px] font-black uppercase tracking-widest text-white/50">{name}</span>
      </div>
      <span className="text-[8px] font-mono text-emerald-400/50 italic">{status}</span>
    </div>
  );
}

function CheckCircle2(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}
