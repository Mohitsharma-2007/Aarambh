import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Database, Zap, CheckCircle2, ChevronRight, 
  Search, Cpu, Box, Share2, Info, X
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface Step1GraphBuildProps {
  currentPhase: number;
  projectData: any;
  graphData: any;
  buildProgress: any;
  onNext: () => void;
  addLog: (msg: string, type?: string) => void;
}

export default function Step1GraphBuild({
  currentPhase,
  projectData,
  graphData,
  buildProgress,
  onNext,
  addLog
}: Step1GraphBuildProps) {
  const [selectedItem, setSelectedItem] = useState<any>(null);

  const stats = useMemo(() => {
    return {
      nodes: graphData?.node_count || graphData?.nodes?.length || 0,
      edges: graphData?.edge_count || graphData?.edges?.length || 0,
      types: projectData?.ontology?.entity_types?.length || 0
    };
  }, [graphData, projectData]);

  const getPhaseStatus = (phase: number) => {
    if (currentPhase > phase) return 'completed';
    if (currentPhase === phase) return 'active';
    return 'pending';
  };

  return (
    <div className="space-y-6 relative">
      {/* Detail Overlay */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="absolute inset-0 z-50 bg-[#090B10]/95 backdrop-blur-md rounded-3xl border border-white/10 overflow-hidden flex flex-col"
          >
            <div className="flex justify-between items-center p-6 border-b border-white/5">
              <div className="flex items-center gap-4">
                <span className="text-[10px] font-black bg-[var(--accent)] text-[#07080C] px-2 py-1 rounded uppercase tracking-widest leading-none">
                  {selectedItem.type.toUpperCase()}
                </span>
                <h3 className="text-lg font-black uppercase text-white/90">{selectedItem.data.name}</h3>
              </div>
              <button 
                onClick={() => setSelectedItem(null)}
                className="p-2 hover:bg-white/5 rounded-xl text-white/40 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar uppercase tracking-tight">
              <div className="space-y-3">
                <h5 className="text-[10px] font-black text-white/20 tracking-widest">Description</h5>
                <p className="text-sm leading-relaxed text-white/60">{selectedItem.data.description || 'No specialized metadata provided.'}</p>
              </div>

              {selectedItem.data.attributes?.length > 0 && (
                <div className="space-y-4">
                  <h5 className="text-[10px] font-black text-white/20 tracking-widest">Attribute Schemas</h5>
                  <div className="grid grid-cols-1 gap-2">
                    {selectedItem.data.attributes.map((attr: any, i: number) => (
                      <div key={i} className="flex justify-between items-center p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-white/80">{attr.name}</span>
                          <span className="text-[9px] text-white/20 font-mono tracking-widest">({attr.type || 'STRING'})</span>
                        </div>
                        <p className="text-[11px] text-white/40 max-w-[200px] text-right italic">{attr.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 gap-6">
        {/* Phase 01: Ontology Generation */}
        <PhaseCard 
          num="01"
          title="Ontology Generation"
          api="POST /api/graph/ontology/generate"
          status={getPhaseStatus(0)}
          isActive={currentPhase === 0}
        >
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed uppercase tracking-tight italic">
              LLM analysis of ingestion stream. Extracting reality seeds & auto-generating schema matrices.
            </p>
            
            {currentPhase === 0 && (
              <div className="flex items-center gap-3 p-4 rounded-2xl bg-[var(--accent)]/5 border border-[var(--accent)]/20 animate-pulse">
                <Cpu className="w-4 h-4 text-[var(--accent)]" />
                <span className="text-[10px] font-black text-[var(--accent)] tracking-widest uppercase">Processing document fragments...</span>
              </div>
            )}

            {projectData?.ontology && (
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2 pt-2">
                  {projectData.ontology.entity_types?.map((ent: any) => (
                    <button 
                      key={ent.name}
                      onClick={() => setSelectedItem({ type: 'entity', data: ent })}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-[9px] font-black uppercase text-white/40 hover:bg-white/10 hover:text-white transition-all shadow-xl"
                    >
                      {ent.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </PhaseCard>

        {/* Phase 02: Graph RAG Build */}
        <PhaseCard 
          num="02"
          title="Neural Mapping (GraphRAG)"
          api="POST /api/graph/build"
          status={getPhaseStatus(1)}
          isActive={currentPhase === 1}
        >
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed uppercase tracking-tight italic">
              Chunking source data & mapping causal relationships. Synchronizing timeline memory buffers.
            </p>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Entities', value: stats.nodes },
                { label: 'Relations', value: stats.edges },
                { label: 'Schemas', value: stats.types },
              ].map(s => (
                <div key={s.label} className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col items-center">
                  <span className="text-lg font-black text-white">{s.value}</span>
                  <span className="text-[8px] font-black uppercase text-white/20 tracking-widest">{s.label}</span>
                </div>
              ))}
            </div>

            {currentPhase === 1 && (
              <div className="space-y-2">
                <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-[var(--accent)]"
                    initial={{ width: 0 }}
                    animate={{ width: `${buildProgress?.progress || 0}%` }}
                  />
                </div>
                <div className="flex justify-between text-[8px] font-black text-white/20 uppercase tracking-widest">
                  <span>Progress Matrix</span>
                  <span>{buildProgress?.progress || 0}% SECURE</span>
                </div>
              </div>
            )}
          </div>
        </PhaseCard>

        {/* Phase 03: Sequence Ready */}
        <PhaseCard 
          num="03"
          title="Deployment Readiness"
          api="STATE :: READY_FOR_SIM"
          status={getPhaseStatus(2)}
          isActive={currentPhase === 2}
        >
          <div className="space-y-6">
            <p className="text-xs text-white/40 leading-relaxed uppercase tracking-tight italic">
              Knowledge Graph verified. Integrity checks passed. Neural channels ready for recursive simulation.
            </p>
            <button 
              onClick={onNext}
              disabled={currentPhase < 2}
              className={cn(
                "w-full h-14 rounded-2xl flex items-center justify-center gap-3 transition-all font-black uppercase tracking-[0.3em] text-[10px]",
                currentPhase >= 2 
                  ? "bg-[var(--accent)] text-[#07080C] shadow-[0_0_30px_rgba(var(--accent-rgb),0.3)] hover:scale-[1.02] active:scale-[0.98]" 
                  : "bg-white/5 text-white/20 italic border border-white/5 cursor-not-allowed"
              )}
            >
              Initialize Simulation Environment <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </PhaseCard>
      </div>
    </div>
  );
}

function PhaseCard({ num, title, api, status, isActive, children }: any) {
  const isCompleted = status === 'completed';
  const isPending = status === 'pending';

  return (
    <motion.div 
      animate={{ opacity: isPending ? 0.3 : 1 }}
      className={cn(
        "glass-card !bg-[#090B10]/40 border-white/10 transition-all duration-500",
        isActive && "border-[var(--accent)]/30 !bg-[var(--accent)]/[0.02] shadow-[0_0_40px_rgba(var(--accent-rgb),0.05)]",
        isCompleted && "border-emerald-500/20"
      )}
    >
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-4">
          <div className={cn(
            "w-12 h-12 rounded-2xl flex items-center justify-center font-black text-lg transition-all",
            isActive ? "bg-[var(--accent)] text-[#07080C]" : 
            isCompleted ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-white/20"
          )}>
            {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : num}
          </div>
          <div>
            <h4 className={cn(
              "text-xs font-black uppercase tracking-widest leading-none mb-1.5",
              isActive ? "text-white" : "text-white/40"
            )}>{title}</h4>
            <span className="text-[8px] font-mono text-white/10 uppercase tracking-widest">{api}</span>
          </div>
        </div>
        <div className={cn(
          "px-2.5 py-1 rounded-full text-[8px] font-black uppercase tracking-widest border",
          isActive ? "border-[var(--accent)]/30 bg-[var(--accent)]/5 text-[var(--accent)]" :
          isCompleted ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400" :
          "border-white/5 bg-white/5 text-white/10"
        )}>
          {status}
        </div>
      </div>
      {children}
    </motion.div>
  );
}
