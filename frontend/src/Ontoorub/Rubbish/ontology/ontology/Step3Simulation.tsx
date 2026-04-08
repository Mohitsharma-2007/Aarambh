import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Globe, MessageSquare, RefreshCcw,
  ChevronRight, Activity, Zap,
  Heart, Repeat2, Search, UserPlus,
  ChevronUp, ChevronDown, Link, MessageCircle, Clock
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { simulationApi, reportApi, requestWithRetry } from '@/api/ontology';

interface Step3SimulationProps {
  simulationId: string;
  maxRounds?: number;
  minutesPerRound?: number;
  projectData: any;
  graphData?: any;
  systemLogs?: any[];
  onBack?: () => void;
  onGoBack?: () => void;
  onNext?: (params?: any) => void;
  onNextStep?: (params?: any) => void;
  onAddLog?: (msg: string) => void;
  onUpdateStatus?: (status: any, simulating?: boolean) => void;
}

// ─── Helpers ──────────────────────────────────────────────
// Matches Vue's checkPlatformsCompleted exactly
function checkPlatformsCompleted(data: any): boolean {
  if (!data) return false;
  const twitterCompleted = data.twitter_completed === true;
  const redditCompleted = data.reddit_completed === true;
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted;
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted;
  if (!twitterEnabled && !redditEnabled) return false;
  if (twitterEnabled && !twitterCompleted) return false;
  if (redditEnabled && !redditCompleted) return false;
  return true;
}

export default function Step3Simulation({
  simulationId,
  maxRounds,
  minutesPerRound = 30,
  projectData,
  graphData,
  systemLogs,
  onBack, onGoBack, onNext, onNextStep,
  onAddLog, onUpdateStatus
}: Step3SimulationProps) {
  // ─── State (matches Vue ref variables) ─────────────────
  const [phase, setPhase] = useState(0); // 0: Not started, 1: Running, 2: Completed
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [runStatus, setRunStatus] = useState<any>({});
  const [allActions, setAllActions] = useState<any[]>([]);

  const actionIdsRef = useRef(new Set<string>());
  const statusTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const detailTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevTwitterRound = useRef(0);
  const prevRedditRound = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const logContentRef = useRef<HTMLDivElement>(null);
  const mountedRef = useRef(true);

  // ─── Computed values ───────────────────────────────────
  const twitterActionsCount = allActions.filter(a => a.platform === 'twitter').length;
  const redditActionsCount = allActions.filter(a => a.platform === 'reddit').length;
  const totalRounds = runStatus.total_rounds || maxRounds || 40;

  const formatElapsedTime = (currentRound: number) => {
    if (!currentRound || currentRound <= 0) return '0h 0m';
    const totalMinutes = currentRound * minutesPerRound;
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${hours}h ${minutes}m`;
  };

  const addLog = useCallback((msg: string) => {
    onAddLog?.(msg);
  }, [onAddLog]);

  // ─── Polling control ───────────────────────────────────
  const stopPolling = useCallback(() => {
    if (statusTimerRef.current) { clearInterval(statusTimerRef.current); statusTimerRef.current = null; }
    if (detailTimerRef.current) { clearInterval(detailTimerRef.current); detailTimerRef.current = null; }
  }, []);

  // ─── Reset all state (matches Vue's resetAllState) ─────
  const resetAllState = useCallback(() => {
    setPhase(0);
    setRunStatus({});
    setAllActions([]);
    actionIdsRef.current = new Set();
    prevTwitterRound.current = 0;
    prevRedditRound.current = 0;
    setStartError(null);
    setIsStarting(false);
    stopPolling();
  }, [stopPolling]);

  // ─── Ingest actions with dedup (matches Vue) ───────────
  const ingestActions = useCallback((serverActions: any[]) => {
    if (!serverActions || !serverActions.length) return;
    const newOnes: any[] = [];
    for (const action of serverActions) {
      const id = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`;
      if (!actionIdsRef.current.has(id)) {
        actionIdsRef.current.add(id);
        newOnes.push({ ...action, _uniqueId: id });
      }
    }
    if (newOnes.length > 0) {
      setAllActions(prev => [...prev, ...newOnes]);
    }
  }, []);

  // ─── Poll 1: Status (lightweight, every 2s) ────────────
  // Uses ref for simulationId to avoid stale closures
  const simIdRef = useRef(simulationId);
  simIdRef.current = simulationId;

  const fetchRunStatus = useCallback(async () => {
    if (!simIdRef.current || !mountedRef.current) return;
    try {
      const res = await simulationApi.getRunStatus(simIdRef.current);
      // axios response: res.data = { success, data: { ... } }
      const payload = res.data;
      if (!payload?.success || !payload?.data) return;
      const data = payload.data;

      setRunStatus(data);

      // Log round changes
      if (data.twitter_current_round > prevTwitterRound.current) {
        addLog(`[Plaza] R${data.twitter_current_round}/${data.total_rounds || maxRounds} | A:${data.twitter_actions_count || 0}`);
        prevTwitterRound.current = data.twitter_current_round;
      }
      if (data.reddit_current_round > prevRedditRound.current) {
        addLog(`[Community] R${data.reddit_current_round}/${data.total_rounds || maxRounds} | A:${data.reddit_actions_count || 0}`);
        prevRedditRound.current = data.reddit_current_round;
      }

      // Check completion (matches Vue logic exactly)
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped';
      const platformsCompleted = checkPlatformsCompleted(data);

      if (isCompleted || platformsCompleted) {
        if (platformsCompleted && !isCompleted) {
          addLog('All platforms completed.');
        }
        addLog('Simulation complete.');
        setPhase(2);
        stopPolling();
        onUpdateStatus?.('completed', false);
      }
    } catch (err) {
      console.warn('fetchRunStatus failed:', err);
    }
  }, [addLog, maxRounds, stopPolling, onUpdateStatus]);

  // ─── Poll 2: Detail (heavier, every 3s) ────────────────
  const fetchRunStatusDetail = useCallback(async () => {
    if (!simIdRef.current || !mountedRef.current) return;
    try {
      const res = await simulationApi.getRunStatusDetail(simIdRef.current);
      const payload = res.data;
      if (payload?.success && payload?.data) {
        const serverActions: any[] = payload.data.all_actions || [];
        ingestActions(serverActions);
        return;
      }
    } catch {
      // detail endpoint may not exist yet — fallback
    }

    // Fallback to getActions
    try {
      const res = await simulationApi.getActions(simIdRef.current, 200);
      const payload = res.data;
      if (payload?.success && payload?.data) {
        const raw = payload.data;
        const serverActions: any[] = Array.isArray(raw) ? raw : (raw?.actions || []);
        ingestActions(serverActions);
      }
    } catch {}
  }, [ingestActions]);

  // ─── Start dual polling ────────────────────────────────
  const startDualPolling = useCallback(() => {
    stopPolling();
    // Immediate first fetch
    fetchRunStatus();
    fetchRunStatusDetail();
    // Then intervals matching Vue: 2s status, 3s detail
    statusTimerRef.current = setInterval(fetchRunStatus, 2000);
    detailTimerRef.current = setInterval(fetchRunStatusDetail, 3000);
  }, [stopPolling, fetchRunStatus, fetchRunStatusDetail]);

  // ─── doStartSimulation ──────────────────────────────────
  // Strategy: CHECK runner status FIRST. Only call start() if not running.
  // The backend's SimulationRunner.start_simulation() throws ValueError
  // if already running, even with force=true (the force logic in the API
  // layer tries to stop first, but the runner's own check races).
  const doStartSimulation = useCallback(async () => {
    if (!simulationId) {
      addLog('Error: Missing simulationId');
      return;
    }

    // Reset UI state
    resetAllState();
    setIsStarting(true);
    setStartError(null);
    onUpdateStatus?.('processing', true);

    try {
      // ── Step 1: Check if simulation is already running ──
      try {
        const statusRes = await simulationApi.getRunStatus(simulationId);
        const statusPayload = statusRes.data;
        console.log('[Step3] getRunStatus response:', JSON.stringify(statusPayload));

        if (statusPayload?.success && statusPayload?.data) {
          const runner = statusPayload.data;
          const runnerStatus = runner.runner_status;

          // Already running → just connect to the live feed
          if (runnerStatus === 'running' || runnerStatus === 'starting' ||
              runner.twitter_running || runner.reddit_running) {
            addLog('Simulation already running. Connecting to live feed...');
            setPhase(1);
            setRunStatus(runner);
            startDualPolling();
            setIsStarting(false);
            return;
          }

          // Already completed → show completed state + load final actions
          if (runnerStatus === 'completed' || runnerStatus === 'stopped' ||
              checkPlatformsCompleted(runner)) {
            addLog('Simulation already completed.');
            setPhase(2);
            setRunStatus(runner);
            onUpdateStatus?.('completed', false);
            fetchRunStatusDetail();
            setIsStarting(false);
            return;
          }

          // Runner exists but idle/failed — ok to start
          addLog(`Runner status: ${runnerStatus}. Proceeding to start...`);
        }
      } catch (checkErr: any) {
        console.log('[Step3] getRunStatus check failed:', checkErr?.message);
        // No runner state yet — fine, proceed to start
      }

      // ── Step 2: Start the simulation ──
      addLog('Starting dual-platform parallel simulation...');

      const hasGraph = !!(graphData?.graph_id || projectData?.graph_id);
      const params: any = {
        simulation_id: simulationId,
        platform: 'parallel',
        force: true,
        ...(hasGraph ? { enable_graph_memory_update: true } : {}),
      };

      if (maxRounds) {
        params.max_rounds = maxRounds;
        addLog(`Max rounds: ${maxRounds}`);
      }

      const res = await requestWithRetry(
        () => simulationApi.start(params),
        3,
        1000
      );

      const payload = res.data;
      if (payload?.success && payload?.data) {
        if (payload.data.force_restarted) {
          addLog('Cleared old logs, restarting...');
        }
        addLog(`Simulation engine started. PID: ${payload.data.process_pid || '-'}`);
        setPhase(1);
        setRunStatus(payload.data);
        startDualPolling();
      } else {
        setStartError(payload?.error || 'Start failed');
        addLog(`Start failed: ${payload?.error || 'Unknown'}`);
        onUpdateStatus?.('error', false);
      }
    } catch (err: any) {
      const responseData = err?.response?.data;
      const errMsg = responseData?.error || responseData?.detail || err?.message || 'Unknown error';
      const statusCode = err?.response?.status;
      console.error('[Simulation Start Error]', { statusCode, responseData, errMsg });

      // "Already running" error → just connect to the feed
      if (statusCode === 400 && typeof errMsg === 'string' &&
          (errMsg.includes('运行') || errMsg.includes('running') || errMsg.includes('sim_'))) {
        addLog('Simulation is active. Connecting to live feed...');
        setPhase(1);
        startDualPolling();
        return;
      }

      setStartError(errMsg);
      addLog(`Start failed (${statusCode || '?'}): ${errMsg}`);
      onUpdateStatus?.('error', false);
    } finally {
      setIsStarting(false);
    }
  }, [simulationId, maxRounds, graphData, projectData, addLog, resetAllState, onUpdateStatus, startDualPolling, fetchRunStatusDetail]);

  // ─── Mount: auto-start ─────────────────────────────────
  // Use a ref guard to prevent React StrictMode double-invocation
  const startedRef = useRef(false);
  useEffect(() => {
    mountedRef.current = true;
    addLog('Step3 Simulation initialized.');
    if (simulationId && !startedRef.current) {
      startedRef.current = true;
      doStartSimulation();
    }
    return () => {
      mountedRef.current = false;
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [simulationId]);

  // Auto-scroll timeline
  useEffect(() => {
    if (scrollRef.current && allActions.length > 0) {
      requestAnimationFrame(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
      });
    }
  }, [allActions.length]);

  // ─── Next step: generate report ────────────────────────
  const handleNext = async () => {
    if (!simulationId || isGeneratingReport) return;
    setIsGeneratingReport(true);
    addLog('Starting report generation...');
    try {
      const res = await reportApi.generate({ simulation_id: simulationId });
      const payload = res.data;
      if (payload?.success && payload?.data) {
        const rptId = payload.data.report_id;
        addLog(`Report task started: ${rptId}`);
        if (onNextStep) onNextStep(rptId);
        else if (onNext) onNext({ reportId: rptId });
      } else {
        addLog(`Report failed: ${payload?.error || 'Unknown error'}`);
        setIsGeneratingReport(false);
      }
    } catch (err: any) {
      addLog(`Report exception: ${err.message}`);
      setIsGeneratingReport(false);
    }
  };

  // ─── Render ────────────────────────────────────────────
  const progressPercent = runStatus.progress_percent || 0;
  const currentRound = Math.max(runStatus.twitter_current_round || 0, runStatus.reddit_current_round || 0);

  return (
    <div className="flex flex-col h-full gap-4 p-4">
      {/* ═══ Header: Platform Status + Controls ═══ */}
      <div className="flex justify-between items-center bg-[#090B10]/70 backdrop-blur-xl p-5 rounded-2xl border border-white/[0.06]">
        <div className="flex gap-3">
          <PlatformCard
            icon={<Globe className="w-3.5 h-3.5 text-blue-400" />}
            name="Info Plaza"
            round={runStatus.twitter_current_round || 0}
            total={totalRounds}
            acts={runStatus.twitter_actions_count || 0}
            elapsed={formatElapsedTime(runStatus.twitter_current_round || 0)}
            active={runStatus.twitter_running}
            completed={runStatus.twitter_completed}
          />
          <PlatformCard
            icon={<MessageSquare className="w-3.5 h-3.5 text-orange-400" />}
            name="Topic Community"
            round={runStatus.reddit_current_round || 0}
            total={totalRounds}
            acts={runStatus.reddit_actions_count || 0}
            elapsed={formatElapsedTime(runStatus.reddit_current_round || 0)}
            active={runStatus.reddit_running}
            completed={runStatus.reddit_completed}
          />
        </div>

        <div className="flex items-center gap-4">
          {phase === 1 && (
            <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="w-24 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                <div className="h-full bg-[var(--accent)] rounded-full transition-all duration-1000" style={{ width: `${progressPercent}%` }} />
              </div>
              <span className="text-[9px] font-mono font-bold text-white/30">R{currentRound}/{totalRounds}</span>
            </div>
          )}

          <button
            onClick={handleNext}
            disabled={phase < 2 || isGeneratingReport}
            className={cn(
              "h-11 px-7 rounded-xl flex items-center gap-2.5 font-black uppercase tracking-[0.12em] text-[10px] transition-all",
              phase >= 2
                ? "bg-[var(--accent)] text-[#07080C] shadow-[0_0_25px_rgba(var(--accent-rgb),0.2)] hover:scale-[1.03] active:scale-[0.97]"
                : "bg-white/[0.04] text-white/15 border border-white/[0.06] cursor-not-allowed"
            )}
          >
            {isGeneratingReport ? <RefreshCcw className="w-3.5 h-3.5 animate-spin" /> : "Synthesize Report"} <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ═══ Live Action Feed ═══ */}
      <div className="flex-1 overflow-hidden flex flex-col rounded-2xl border border-white/[0.06] bg-[#090B10]/50">
        {/* Feed header */}
        <div className="px-5 py-3 border-b border-white/[0.06] flex justify-between items-center bg-white/[0.01]">
          <div className="flex items-center gap-2.5">
            <div className={cn(
              "w-1.5 h-1.5 rounded-full",
              phase === 1 ? "bg-[var(--accent)] animate-pulse shadow-[0_0_6px_var(--accent)]"
                : phase === 2 ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]"
                : "bg-white/15"
            )} />
            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/60">
              {phase === 2 ? 'Simulation Complete' : phase === 1 ? 'Live Action Feed' : isStarting ? 'Starting...' : 'Waiting...'}
            </h3>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[9px] font-mono text-white/20">
              {allActions.length} events
              {allActions.length > 0 && (
                <span className="ml-2">
                  <span className="text-blue-400/40">{twitterActionsCount}</span>
                  <span className="text-white/10 mx-1">/</span>
                  <span className="text-orange-400/40">{redditActionsCount}</span>
                </span>
              )}
            </span>
            {phase === 1 && <span className="text-[8px] font-black text-[var(--accent)]/60 uppercase tracking-widest animate-pulse">Live</span>}
          </div>
        </div>

        {/* Feed body */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar" ref={scrollRef}>
          <AnimatePresence initial={false}>
            {allActions.length === 0 ? (
              <EmptyState phase={phase} isStarting={isStarting} error={startError} />
            ) : (
              <div className="space-y-2 relative">
                {/* Timeline spine */}
                <div className="absolute left-[14px] top-0 bottom-0 w-px bg-white/[0.03]" />
                {allActions.map((action) => (
                  <ActionCard key={action._uniqueId} action={action} />
                ))}
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/* ═══════════ Sub-Components ═══════════ */

function EmptyState({ phase, isStarting, error }: { phase: number; isStarting: boolean; error: string | null }) {
  const label = error
    ? `Error: ${error}`
    : isStarting
    ? 'Starting simulation engine...'
    : phase === 1
    ? 'Connected — waiting for first actions...'
    : phase === 2
    ? 'No actions recorded.'
    : 'Initializing...';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col items-center justify-center gap-5">
      <div className="relative">
        {error ? (
          <Activity className="w-8 h-8 text-red-400/30" />
        ) : phase === 1 || isStarting ? (
          <Zap className="w-8 h-8 text-[var(--accent)]/20 animate-pulse" />
        ) : (
          <Activity className="w-8 h-8 text-white/[0.06]" />
        )}
      </div>
      <span className={cn(
        "text-[10px] font-black uppercase tracking-[0.3em] text-center max-w-xs",
        error ? "text-red-400/30" : "text-white/[0.1]"
      )}>{label}</span>
      {(phase === 1 || isStarting) && !error && (
        <div className="flex gap-1">
          {[0, 1, 2].map(i => (
            <div key={i} className="w-1 h-1 rounded-full bg-[var(--accent)]/30 animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
          ))}
        </div>
      )}
    </motion.div>
  );
}

function PlatformCard({ icon, name, round, total, acts, elapsed, active, completed }: any) {
  return (
    <div className={cn(
      "px-4 py-2.5 rounded-xl border transition-all min-w-[180px]",
      active ? "border-[var(--accent)]/15 bg-[var(--accent)]/[0.02]" :
        completed ? "border-emerald-500/15 bg-emerald-500/[0.02]" : "border-white/[0.05] bg-white/[0.01]"
    )}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-[9px] font-black uppercase tracking-widest text-white/35">{name}</span>
        </div>
        {completed && <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_5px_rgba(52,211,153,0.4)]" />}
        {active && !completed && <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />}
      </div>
      <div className="flex gap-5">
        <div>
          <span className="text-[7px] font-black text-white/[0.07] tracking-widest uppercase block">Round</span>
          <span className="text-xs font-black text-white/80">{round}<span className="text-[8px] text-white/15 ml-0.5">/{total}</span></span>
        </div>
        <div>
          <span className="text-[7px] font-black text-white/[0.07] tracking-widest uppercase block">Time</span>
          <span className="text-xs font-black text-white/80">{elapsed}</span>
        </div>
        <div>
          <span className="text-[7px] font-black text-white/[0.07] tracking-widest uppercase block">Acts</span>
          <span className="text-xs font-black text-white/80">{acts}</span>
        </div>
      </div>
    </div>
  );
}

function ActionCard({ action }: { action: any }) {
  const isTwitter = action.platform === 'twitter';
  const actionType = action.action_type || '';

  const typeColors: Record<string, string> = {
    'CREATE_POST': 'bg-emerald-500/10 text-emerald-400/80',
    'QUOTE_POST': 'bg-blue-500/10 text-blue-400/80',
    'REPOST': 'bg-violet-500/10 text-violet-400/80',
    'LIKE_POST': 'bg-pink-500/10 text-pink-400/80',
    'CREATE_COMMENT': 'bg-amber-500/10 text-amber-400/80',
    'UPVOTE_POST': 'bg-emerald-500/10 text-emerald-400/60',
    'DOWNVOTE_POST': 'bg-red-500/10 text-red-400/60',
    'FOLLOW': 'bg-cyan-500/10 text-cyan-400/80',
    'SEARCH_POSTS': 'bg-white/[0.04] text-white/30',
    'DO_NOTHING': 'bg-white/[0.02] text-white/15',
  };

  const typeLabels: Record<string, string> = {
    'CREATE_POST': 'POST', 'QUOTE_POST': 'QUOTE', 'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE', 'CREATE_COMMENT': 'COMMENT', 'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE', 'FOLLOW': 'FOLLOW', 'SEARCH_POSTS': 'SEARCH',
    'DO_NOTHING': 'IDLE', 'LIKE_COMMENT': 'LIKE',
  };

  // Render action-specific content (matches Vue template)
  const renderContent = () => {
    const args = action.action_args || {};

    switch (actionType) {
      case 'CREATE_POST':
        return args.content ? <p className="text-[11px] text-white/50 leading-relaxed">{args.content}</p> : null;

      case 'QUOTE_POST':
        return (
          <>
            {args.quote_content && <p className="text-[11px] text-white/50 leading-relaxed mb-2">{args.quote_content}</p>}
            {args.original_content && (
              <div className="p-2.5 rounded-lg bg-white/[0.02] border-l-2 border-white/[0.06]">
                <div className="flex items-center gap-1.5 mb-1 text-[9px] text-white/20">
                  <Link className="w-3 h-3" />
                  <span>@{args.original_author_name || 'User'}</span>
                </div>
                <p className="text-[10px] text-white/25 italic line-clamp-2">{args.original_content}</p>
              </div>
            )}
          </>
        );

      case 'REPOST':
        return (
          <>
            <div className="flex items-center gap-1.5 text-[10px] text-white/25 mb-1">
              <Repeat2 className="w-3.5 h-3.5" />
              <span>Reposted from @{args.original_author_name || 'User'}</span>
            </div>
            {args.original_content && (
              <p className="text-[10px] text-white/20 pl-5 line-clamp-3">{args.original_content}</p>
            )}
          </>
        );

      case 'LIKE_POST':
        return (
          <>
            <div className="flex items-center gap-1.5 text-[10px] text-pink-400/30 mb-1">
              <Heart className="w-3 h-3 fill-current" />
              <span>Liked @{args.post_author_name || 'User'}'s post</span>
            </div>
            {args.post_content && (
              <p className="text-[10px] text-white/15 italic line-clamp-2">"{truncate(args.post_content, 120)}"</p>
            )}
          </>
        );

      case 'CREATE_COMMENT':
        return (
          <>
            {args.content && <p className="text-[11px] text-white/50 leading-relaxed mb-1">{args.content}</p>}
            {args.post_id && (
              <div className="flex items-center gap-1.5 text-[9px] text-white/15">
                <MessageCircle className="w-3 h-3" />
                <span>Reply to post #{args.post_id}</span>
              </div>
            )}
          </>
        );

      case 'SEARCH_POSTS':
        return (
          <div className="flex items-center gap-1.5 text-[10px] text-white/25">
            <Search className="w-3.5 h-3.5" />
            <span>Search: </span>
            <span className="font-mono bg-white/[0.04] px-1.5 py-0.5 rounded text-[9px]">"{args.query || ''}"</span>
          </div>
        );

      case 'FOLLOW':
        return (
          <div className="flex items-center gap-1.5 text-[10px] text-cyan-400/30">
            <UserPlus className="w-3.5 h-3.5" />
            <span>Followed @{args.target_user || args.user_id || 'User'}</span>
          </div>
        );

      case 'UPVOTE_POST':
      case 'DOWNVOTE_POST':
        return (
          <>
            <div className="flex items-center gap-1.5 text-[10px] text-white/25">
              {actionType === 'UPVOTE_POST' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              <span>{actionType === 'UPVOTE_POST' ? 'Upvoted' : 'Downvoted'} Post</span>
            </div>
            {args.post_content && (
              <p className="text-[10px] text-white/15 italic mt-1 line-clamp-2">"{truncate(args.post_content, 120)}"</p>
            )}
          </>
        );

      case 'DO_NOTHING':
        return (
          <div className="flex items-center gap-1.5 text-[10px] text-white/15">
            <Clock className="w-3 h-3" />
            <span>Action Skipped</span>
          </div>
        );

      default:
        // Fallback for unknown types
        return args.content ? <p className="text-[11px] text-white/40 leading-relaxed">{args.content}</p> : null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex gap-3 group relative"
    >
      {/* Timeline dot */}
      <div className="w-5 flex-shrink-0 flex justify-center pt-3 relative z-10">
        <div className={cn(
          "w-2 h-2 rounded-full ring-2 ring-[#090B10]",
          isTwitter ? "bg-blue-400" : "bg-orange-400"
        )} />
      </div>

      {/* Card */}
      <div className="flex-1 p-3.5 rounded-xl bg-white/[0.015] border border-white/[0.04] group-hover:border-white/[0.07] group-hover:bg-white/[0.02] transition-all">
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center gap-2.5">
            <div className={cn(
              "w-6 h-6 rounded-md flex items-center justify-center text-[8px] font-black italic border",
              isTwitter ? "bg-blue-500/5 border-blue-500/10 text-blue-400/50" : "bg-orange-500/5 border-orange-500/10 text-orange-400/50"
            )}>
              {(action.agent_name || 'A')[0]}
            </div>
            <div>
              <span className="text-[10px] font-black text-white/60 leading-none block">{action.agent_name || 'Agent'}</span>
              <span className="text-[7px] font-mono text-white/12 uppercase tracking-wider">{action.platform} R{action.round_num}</span>
            </div>
          </div>
          <span className={cn(
            "px-1.5 py-0.5 rounded text-[7px] font-black uppercase tracking-wider",
            typeColors[actionType] || "bg-white/[0.03] text-white/20"
          )}>
            {typeLabels[actionType] || actionType || '?'}
          </span>
        </div>

        {renderContent()}

        {/* Timestamp footer */}
        <div className="mt-2 flex justify-end">
          <span className="text-[8px] font-mono text-white/[0.08]">
            R{action.round_num} • {formatActionTime(action.timestamp)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Utility functions ───────────────────────────────────
function truncate(content: string | undefined, maxLength: number): string {
  if (!content) return '';
  return content.length > maxLength ? content.substring(0, maxLength) + '...' : content;
}

function formatActionTime(timestamp: string | undefined): string {
  if (!timestamp) return '';
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return ''; }
}
