import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, BarChart3, Database, Globe, Users, Zap, 
  ChevronDown, ChevronUp, CheckCircle2, RefreshCcw,
  ArrowRight, Terminal, Info, Layout, BookOpen
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { reportApi } from '@/api/ontology';
import ReactMarkdown from 'react-markdown';

interface Step4ReportProps {
  reportId: string;
  simulationId: string;
  onNext: () => void;
}

export default function Step4Report({
  reportId,
  simulationId,
  onNext
}: Step4ReportProps) {
  const [outline, setOutline] = useState<any>(null);
  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [generatedSections, setGeneratedSections] = useState<Record<number, string>>({});
  const [currentSectionIndex, setCurrentSectionIndex] = useState(1);
  const [isComplete, setIsComplete] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState(new Set());
  
  const timerRef = useRef<any>(null);

  useEffect(() => {
    if (reportId) startPolling();
    return () => stopPolling();
  }, [reportId]);

  const startPolling = () => {
    timerRef.current = setInterval(async () => {
      try {
        const res = await reportApi.getAgentLog(reportId);
        if (res.data.success) {
          const logs = res.data.data.logs || [];
          setAgentLogs(logs);
          
          // Update outline from planning_complete log
          const planLog = logs.find((l: any) => l.action === 'planning_complete');
          if (planLog?.details?.outline) setOutline(planLog.details.outline);

          // Build generated sections
          const newSections: Record<number, string> = {};
          logs.forEach((l: any) => {
            if (l.action === 'section_content' && l.details?.content) {
              newSections[l.section_index] = l.details.content;
            }
          });
          setGeneratedSections(newSections);

          // Update current index
          const lastStart = [...logs].reverse().find((l: any) => l.action === 'section_start');
          if (lastStart) setCurrentSectionIndex(lastStart.section_index);

          if (logs.some((l: any) => l.action === 'report_complete')) {
            setIsComplete(true);
            stopPolling();
          }
        }
      } catch (err) { console.warn(err); }
    }, 2000);
  };

  const stopPolling = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const toggleSection = (idx: number) => {
    const newSet = new Set(collapsedSections);
    if (newSet.has(idx)) newSet.delete(idx);
    else newSet.add(idx);
    setCollapsedSections(newSet);
  };

  return (
    <div className="flex h-full gap-6 overflow-hidden">
      {/* Left Panel: The Report Document */}
      <div className="flex-1 bg-[#090B10]/40 rounded-3xl border border-white/5 overflow-y-auto custom-scrollbar p-10 space-y-10 relative">
        {!outline ? (
           <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-20">
             <BookOpen className="w-16 h-16 animate-pulse" />
             <span className="text-xs font-black uppercase tracking-[0.5em]">Decompiling Simulation Data...</span>
           </div>
        ) : (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto">
            <header className="space-y-4 mb-16 border-b border-white/5 pb-16">
              <div className="flex items-center gap-3">
                <span className="px-2 py-1 bg-[var(--accent)] text-[#07080C] text-[8px] font-black uppercase tracking-widest rounded-sm">Ontology Insight</span>
                <span className="text-[9px] font-mono text-white/20 uppercase">RPT :: {reportId}</span>
              </div>
              <h1 className="text-4xl font-black text-white uppercase tracking-tight leading-none">{outline.title}</h1>
              <p className="text-sm text-white/40 leading-relaxed italic border-l-2 border-[var(--accent)]/30 pl-6 uppercase tracking-tight">
                {outline.summary}
              </p>
            </header>

            <div className="space-y-8">
              {outline.sections.map((section: any, i: number) => {
                const idx = i + 1;
                const content = generatedSections[idx];
                const isActive = currentSectionIndex === idx;
                const isCompleted = !!content;

                return (
                  <section key={idx} className={cn(
                    "rounded-3xl border transition-all duration-500 overflow-hidden",
                    isActive ? "bg-[var(--accent)]/[0.02] border-[var(--accent)]/30 shadow-[0_0_50px_rgba(var(--accent-rgb),0.03)]" : 
                    isCompleted ? "bg-white/[0.01] border-white/10" : "bg-white/[0.01] border-white/5 opacity-30"
                  )}>
                    <div className="p-6 flex justify-between items-center cursor-pointer hover:bg-white/[0.02]" onClick={() => toggleSection(i)}>
                      <div className="flex items-center gap-4">
                        <span className="text-xs font-black text-white/20 font-mono tracking-tighter">0{idx}</span>
                        <h3 className="text-sm font-black text-white/80 uppercase tracking-widest">{section.title}</h3>
                      </div>
                      <div className="flex items-center gap-4">
                        {isCompleted && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                        {isActive && !isCompleted && <RefreshCcw className="w-4 h-4 text-[var(--accent)] animate-spin" />}
                        <ChevronDown className={cn("w-4 h-4 text-white/20 transition-transform", collapsedSections.has(i) && "-rotate-90")} />
                      </div>
                    </div>
                    
                    {!collapsedSections.has(i) && (
                      <div className="p-10 pt-0 text-white/60 text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
                        {content ? (
                           <ReactMarkdown>{content}</ReactMarkdown>
                        ) : isActive ? (
                          <div className="flex items-center gap-3 py-10 opacity-30 italic uppercase text-[10px] tracking-widest">
                            <span className="w-4 h-px bg-white/20" /> Synthesizing section narratives...
                          </div>
                        ) : null}
                      </div>
                    )}
                  </section>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>

      {/* Right Panel: Synthesis Engine Logs */}
      <div className="w-[450px] flex flex-col gap-6">
        <div className="flex-1 bg-[#090B10]/60 rounded-3xl border border-white/5 backdrop-blur-xl flex flex-col shadow-2xl overflow-hidden">
          <div className="p-6 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Terminal className="w-4 h-4 text-[var(--accent)]" />
              <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/80">Synthesis Monitor</h3>
            </div>
            {isComplete && (
              <span className="text-[8px] font-black bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20 uppercase">Complete</span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-4">
             {agentLogs.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center opacity-10 gap-4">
                   <Zap className="w-10 h-10 animate-pulse" />
                   <span className="text-[9px] font-black uppercase tracking-[0.5em]">Awaiting Uplink...</span>
                </div>
             ) : (
               agentLogs.map((log, i) => (
                 <motion.div 
                   initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                   key={i} 
                   className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2 relative group hover:border-white/10 transition-all"
                 >
                   <div className="flex justify-between items-start">
                     <span className={cn(
                       "text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded",
                       log.action === 'tool_call' ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" :
                       log.action === 'report_complete' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                       "bg-white/5 text-white/40"
                     )}>
                       {log.action.replace('_', ' ')}
                     </span>
                     <span className="text-[8px] font-mono text-white/10">{new Date(log.timestamp).toLocaleTimeString()}</span>
                   </div>
                   
                   <p className="text-[10px] text-white/50 leading-relaxed uppercase italic">
                     {log.details?.message || log.details?.tool_name || log.section_title || "Processing neural weights..."}
                   </p>

                   {log.action === 'tool_call' && log.details?.parameters && (
                      <div className="mt-2 text-[9px] bg-black/40 p-2 rounded-lg border border-white/5 text-white/20 font-mono overflow-auto max-h-20 whitespace-pre">
                        {JSON.stringify(log.details.parameters, null, 2)}
                      </div>
                   )}
                 </motion.div>
               ))
             )}
          </div>

          {isComplete && (
            <div className="p-6 bg-white/[0.02] border-t border-white/5">
              <button 
                onClick={onNext}
                className="w-full h-14 bg-[var(--accent)] text-[#07080C] rounded-2xl flex items-center justify-center gap-3 font-black uppercase tracking-[0.4em] text-[10px] hover:scale-[1.02] transition-all shadow-[0_0_40px_rgba(var(--accent-rgb),0.3)]"
              >
                Launch Interaction Node <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
