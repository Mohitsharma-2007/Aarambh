import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Users, MessageSquare, Terminal, ChevronDown,
  Search, CheckCircle2, Shield, Info, Activity, Globe,
  Layout, BookOpen, Bot, RefreshCcw
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { reportApi, simulationApi } from '@/api/ontology';
import ReactMarkdown from 'react-markdown';

interface Step5InteractionProps {
  reportId: string;
  simulationId: string;
}

export default function Step5Interaction({
  reportId,
  simulationId
}: Step5InteractionProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'survey'>('chat');
  const [chatTarget, setChatTarget] = useState<'report' | 'agent'>('report');
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [showAgentList, setShowAgentList] = useState(false);

  // Survey State
  const [selectedAgents, setSelectedAgents] = useState<Set<number>>(new Set());
  const [surveyInput, setSurveyInput] = useState('');
  const [surveyResults, setSurveyResults] = useState<any[]>([]);
  const [isSurveying, setIsSurveying] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (simulationId) loadProfiles();
  }, [simulationId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isSending]);

  const loadProfiles = async () => {
    try {
      const res = await simulationApi.getProfiles(simulationId);
      if (res.data.success) setProfiles(res.data.data || []);
    } catch (err) { console.error(err); }
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSending) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: msg, timestamp: new Date().toISOString() }]);
    setIsSending(true);

    try {
      let res;
      if (chatTarget === 'report') {
        res = await reportApi.chat({ report_id: reportId, message: msg });
      } else {
        res = await simulationApi.interviewAgents({
          simulation_id: simulationId,
          agent_ids: [profiles.indexOf(selectedAgent).toString()],
          questions: [msg]
        });
      }

      if (res.data.success) {
        const data = res.data.data;
        // Handle both chat and interview response formats
        const reply = data.response || data.answer || (data.results ? Object.values(data.results)[0] as string : "Neural node silent.");
        setChatHistory(prev => [...prev, { role: 'assistant', content: reply, timestamp: new Date().toISOString() }]);
      }
    } catch (err) { console.error(err); }
    finally { setIsSending(false); }
  };

  const handleSurvey = async () => {
    if (!surveyInput.trim() || selectedAgents.size === 0 || isSurveying) return;
    setIsSurveying(true);
    try {
      const agentIds = Array.from(selectedAgents).map(idx => idx.toString());
      const res = await simulationApi.interviewAgents({
        simulation_id: simulationId,
        agent_ids: agentIds,
        questions: [surveyInput]
      });
      if (res.data.success) {
        // Transform results for list
        const results = Object.entries(res.data.data.results || {}).map(([key, val]: any) => ({
          agent_name: profiles[parseInt(key)]?.username || 'Unknown',
          answer: typeof val === 'string' ? val : (val.response || val.answer)
        }));
        setSurveyResults(results);
      }
    } catch (err) { console.error(err); }
    finally { setIsSurveying(false); }
  };

  return (
    <div className="flex h-full gap-6 overflow-hidden">
      {/* Left Navigation / Agent Selection */}
      <div className="w-[350px] flex flex-col gap-6">
        <div className="flex-1 bg-[#090B10]/60 rounded-3xl border border-white/5 backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden">
          <div className="p-6 space-y-4">
            <div className="flex bg-white/5 p-1 rounded-2xl border border-white/5">
              <button
                onClick={() => setActiveTab('chat')}
                className={cn("flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all", activeTab === 'chat' ? "bg-[var(--accent)] text-[#07080C]" : "text-white/20 hover:text-white/40")}
              >
                Neural Chat
              </button>
              <button
                onClick={() => setActiveTab('survey')}
                className={cn("flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all", activeTab === 'survey' ? "bg-[var(--accent)] text-[#07080C]" : "text-white/20 hover:text-white/40")}
              >
                World Survey
              </button>
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/20" />
              <input
                type="text" placeholder="FILTER ENTITIES..."
                className="w-full h-12 bg-white/[0.02] border border-white/5 rounded-xl pl-11 pr-4 text-[10px] font-bold text-white uppercase tracking-widest focus:outline-none focus:border-[var(--accent)]/30 transition-all pointer-events-none opacity-50"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 custom-scrollbar space-y-2 pb-6">
            <button
              onClick={() => { setChatTarget('report'); setSelectedAgent(null); setActiveTab('chat'); }}
              className={cn(
                "w-full p-4 rounded-2xl border transition-all flex items-center gap-4 group text-left",
                chatTarget === 'report' ? "border-[var(--accent)]/30 bg-[var(--accent)]/[0.03]" : "border-white/5 bg-white/[0.01] hover:bg-white/[0.03]"
              )}
            >
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                <Bot className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h4 className="text-[10px] font-black text-white uppercase tracking-widest">Report Architect</h4>
                <p className="text-[8px] text-white/20 uppercase font-bold italic">Central Intelligence Node</p>
              </div>
            </button>

            <div className="pt-4 px-2 mb-2">
              <span className="text-[8px] font-black text-white/10 uppercase tracking-[0.3em]">Simulation Population</span>
            </div>

            {profiles.map((p, i) => (
              <button
                key={i}
                onClick={() => {
                  if (activeTab === 'chat') { setChatTarget('agent'); setSelectedAgent(p); }
                  else {
                    const next = new Set(selectedAgents);
                    if (next.has(i)) next.delete(i); else next.add(i);
                    setSelectedAgents(next);
                  }
                }}
                className={cn(
                  "w-full p-4 rounded-2xl border transition-all flex items-center justify-between group",
                  (activeTab === 'chat' && selectedAgent === p) || (activeTab === 'survey' && selectedAgents.has(i))
                    ? "border-[var(--accent)]/30 bg-[var(--accent)]/[0.03]"
                    : "border-white/5 bg-white/[0.01] hover:bg-white/[0.03]"
                )}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center border border-white/10 text-[10px] font-black text-white/40 italic group-hover:text-white/60 transition-colors">
                    {(p.username || 'A')[0]}
                  </div>
                  <div className="text-left">
                    <h4 className={cn("text-[10px] font-black uppercase tracking-widest transition-colors", (activeTab === 'chat' && selectedAgent === p) ? "text-[var(--accent)]" : "text-white/60")}>{p.username}</h4>
                    <p className="text-[8px] text-white/20 uppercase font-bold truncate w-32 tracking-tighter">{p.profession}</p>
                  </div>
                </div>
                {activeTab === 'survey' && (
                  <div className={cn("w-4 h-4 rounded-full border border-white/10 flex items-center justify-center transition-all", selectedAgents.has(i) ? "bg-[var(--accent)] border-[var(--accent)]" : "")}>
                    {selectedAgents.has(i) && <CheckCircle2 className="w-3 h-3 text-[#07080C]" />}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Interaction Area */}
      <div className="flex-1 bg-[#090B10]/40 rounded-3xl border border-white/5 backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden relative">
        <AnimatePresence mode="wait">
          {activeTab === 'chat' ? (
            <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col h-full uppercase tracking-tight">
              <div className="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse shadow-[0_0_10px_var(--accent)]" />
                  <div>
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Neural Uplink Interface</h3>
                    <p className="text-[8px] text-white/20 italic font-bold">MODE :: {chatTarget === 'report' ? 'Architectural Query' : 'Entity Interrogation'}</p>
                  </div>
                </div>
                {selectedAgent && (
                  <div className="text-right">
                    <span className="text-[9px] font-black text-[var(--accent)] block">TARGETING: {selectedAgent.username}</span>
                    <span className="text-[8px] text-white/20 font-mono tracking-widest">STANCE :: {selectedAgent.stance || 'NEUTRAL'}</span>
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-8">
                {chatHistory.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center opacity-10 gap-6">
                    <Bot className="w-20 h-20" />
                    <p className="text-xs font-black uppercase tracking-[0.5em] text-center max-w-sm leading-relaxed">Establish neural handshake to interrogate the simulation results.</p>
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div key={i} className={cn("flex gap-6", msg.role === 'user' ? "flex-row-reverse" : "flex-row")}>
                      <div className={cn("w-10 h-10 rounded-2xl flex items-center justify-center border font-black text-xs", msg.role === 'user' ? "bg-white/5 border-white/10 text-white/20 italic" : "bg-[var(--accent)]/10 border-[var(--accent)]/20 text-[var(--accent)]")}>
                        {msg.role === 'user' ? 'U' : chatTarget === 'report' ? 'R' : selectedAgent?.username?.[0] || 'A'}
                      </div>
                      <div className={cn(
                        "max-w-[70%] p-6 rounded-3xl text-sm leading-relaxed",
                        msg.role === 'user' ? "bg-white/[0.03] text-white/80 rounded-tr-none" : "bg-white/[0.01] border border-white/5 text-white/60 rounded-tl-none prose prose-invert prose-sm"
                      )}>
                        {msg.role === 'user' ? msg.content : <ReactMarkdown>{msg.content}</ReactMarkdown>}
                      </div>
                    </div>
                  ))
                )}
                {isSending && (
                  <div className="flex gap-6">
                    <div className="w-10 h-10 rounded-2xl bg-[var(--accent)]/10 border border-[var(--accent)]/20 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-[var(--accent)] animate-spin-slow" />
                    </div>
                    <div className="flex gap-2 items-center px-6 italic text-[10px] text-white/20">
                      <span className="animate-pulse">THINKING...</span>
                      <span className="w-1 h-1 bg-white/20 rounded-full animate-bounce delay-75" />
                      <span className="w-1 h-1 bg-white/20 rounded-full animate-bounce delay-150" />
                      <span className="w-1 h-1 bg-white/20 rounded-full animate-bounce delay-300" />
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="p-8 bg-white/[0.02] border-t border-white/5">
                <div className="relative group">
                  <textarea
                    value={chatInput} onChange={e => setChatInput(e.target.value)}
                    placeholder="Input query for the neural network..."
                    className="w-full bg-white/[0.02] border border-white/5 rounded-2xl p-6 pr-20 text-xs font-bold text-white focus:outline-none focus:border-[var(--accent)]/30 min-h-[100px] transition-all resize-none uppercase placeholder:text-white/10"
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSendMessage())}
                  />
                  <button
                    onClick={handleSendMessage} disabled={!chatInput.trim() || isSending}
                    className="absolute right-4 bottom-4 w-12 h-12 bg-[var(--accent)] text-[#07080C] rounded-xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-[0_0_20px_rgba(var(--accent-rgb),0.2)] disabled:opacity-20 disabled:scale-100"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div key="survey" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col h-full uppercase tracking-tight">
              <div className="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse shadow-[0_0_10px_#f97316]" />
                  <div>
                    <h3 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Population Consensus Survey</h3>
                    <p className="text-[8px] text-white/20 italic font-bold">MODE :: Batch Interrogation</p>
                  </div>
                </div>
                <span className="text-[9px] font-black text-orange-400 bg-orange-500/10 px-3 py-1 rounded border border-orange-500/20">{selectedAgents.size} NODES TARGETED</span>
              </div>

              <div className="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-8">
                {surveyResults.length === 0 ? (
                  <div className="space-y-8">
                    <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/5 space-y-6">
                      <div className="flex gap-4">
                        <Info className="w-4 h-4 text-orange-400 mt-1" />
                        <p className="text-[10px] text-white/40 leading-relaxed font-bold uppercase tracking-widest">
                          Configure a thematic query to dispatch to the selected agent population. The engine will aggregate individual neural responses into a consensus set.
                        </p>
                      </div>
                      <textarea
                        value={surveyInput} onChange={e => setSurveyInput(e.target.value)}
                        placeholder="WHAT IS YOUR STANCE ON THE PROJECTED MARKET VOLATILITY?"
                        className="w-full bg-black/40 border border-white/5 rounded-2xl p-6 text-xs font-bold text-white focus:outline-none focus:border-orange-500/30 min-h-[120px] transition-all resize-none uppercase"
                      />
                      <button
                        onClick={handleSurvey} disabled={!surveyInput.trim() || selectedAgents.size === 0 || isSurveying}
                        className="w-full h-14 bg-orange-500 text-white rounded-2xl flex items-center justify-center gap-3 font-black uppercase tracking-[0.4em] text-[10px] hover:scale-[1.02] transition-all disabled:opacity-20"
                      >
                        {isSurveying ? <RefreshCcw className="w-4 h-4 animate-spin" /> : "Dispatch Batch Query"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4">
                    {surveyResults.map((res, i) => (
                      <div key={i} className="p-6 rounded-3xl bg-white/[0.01] border border-white/5 space-y-4">
                        <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                          <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-[10px] font-black text-white/30 italic">{res.agent_name[0]}</div>
                          <span className="text-[10px] font-black text-white/60 tracking-widest uppercase">{res.agent_name}</span>
                        </div>
                        <div className="text-xs text-white/50 leading-relaxed prose prose-invert prose-sm">
                          <ReactMarkdown>{res.answer}</ReactMarkdown>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
