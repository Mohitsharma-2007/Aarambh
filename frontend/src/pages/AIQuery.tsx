import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from "framer-motion";
import { 
  Send, Loader2, Sparkles, Database, Zap, ExternalLink, 
  MessageSquare, Plus, Trash2, Copy, Download, Bot,
  BrainCircuit, Clock, Globe, TrendingUp, BarChart3, 
  Search, FileText, ChevronRight, Activity, Shield, 
  Terminal, Cpu, Layers, Layout, Maximize2, List
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { api } from '@/api';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

// --- CONFIG ---
const FINANCE_API = "http://localhost:8000";
const NEWS_API = "http://localhost:8000";

interface Source {
  title: string;
  url: string;
  snippet: string;
  source_type: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export default function AIQuery() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  
  // Real-time Intelligence State
  const [movers, setMovers] = useState<any[]>([]);
  const [headlines, setHeadlines] = useState<any[]>([]);
  const [geoAlerts, setGeoAlerts] = useState<any[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchConversations();
    fetchIntel();
    const intelIv = setInterval(fetchIntel, 60000);
    return () => clearInterval(intelIv);
  }, []);

  const fetchIntel = async () => {
    try {
      const [mRes, nRes, gRes] = await Promise.all([
        axios.get(`${FINANCE_API}/api/yahoo-finance/movers`, { params: { type: "most_actives" } }).catch(() => null),
        axios.get(`${NEWS_API}/api/news/headlines`).catch(() => null),
        axios.get(`${NEWS_API}/api/geo/all`).catch(() => null)
      ]);
      if (mRes?.data?.movers) setMovers(mRes.data.movers.slice(0, 5));
      if (nRes?.data?.articles) setHeadlines(nRes.data.articles.slice(0, 5));
      if (gRes?.data?.articles) setGeoAlerts(gRes.data.articles.slice(0, 3));
    } catch (e) { console.warn("Intel fetch failed", e); }
  };

  const fetchConversations = async () => {
    try {
      const res = await api.getConversations();
      if (res?.conversations) setConversations(res.conversations);
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const systemContext = `[SYSTEM ROLE: You are an AARAMBH Ontology Specialist and Professional Financial Intelligence Analyst. Provide deep, structural insights into market events, news, and complex systems. Analyze relationships between entities, detect risk vectors, and synthesize information with professional rigor. Maintain a high-fidelity, analytical tone. Use data-driven reasoning.]\n\n`;
      
      const response = await api.sendChatMessage({
        message: (messages.length === 0 ? systemContext : '') + userMessage.content,
        conversation_id: activeConversation || undefined,
      });

      if (response) {
        const fullContent = response.content || 'Analytical uplink severed. Request retry.';
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: fullContent,
          timestamp: new Date(),
          sources: response.sources,
        };

        setMessages(prev => [...prev, assistantMessage]);
        if (response.conversation_id && !activeConversation) {
          setActiveConversation(response.conversation_id);
          fetchConversations();
        }
      }
    } catch (err) {
      toast.error('Synthesis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen bg-[#07080C] text-white flex overflow-hidden selection:bg-[var(--accent)]/30 font-sans">
      {/* Dynamic Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-[var(--accent)]/5 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-500/5 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* LEFT SIDEBAR: History & Intel */}
      <aside 
        className={cn(
          "relative z-30 border-r border-white/5 bg-[#090B10]/80 backdrop-blur-2xl transition-all duration-500 flex flex-col pt-4 overflow-hidden",
          sidebarOpen ? "w-[380px]" : "w-0"
        )}
      >
        <div className="flex-1 overflow-y-auto px-6 space-y-10 py-6 custom-scrollbar">
           {/* Section 1: New Query */}
           <button 
             onClick={() => { setMessages([]); setActiveConversation(null); }}
             className="w-full h-14 bg-[var(--accent)] text-[#07080C] rounded-2xl flex items-center justify-center gap-3 font-black uppercase tracking-[0.2em] text-[10px] hover:scale-[1.02] transition-all shadow-[0_0_40px_rgba(var(--accent-rgb),0.2)]"
           >
             <Plus className="w-4 h-4" /> Start New Synthesis
           </button>

           {/* Section 2: Market Movers Submerged */}
           <div className="space-y-4">
              <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-[0.3em] text-white/20 px-2">
                 <span>Market Vectors</span>
                 <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
              </div>
              <div className="space-y-2">
                {movers.map((m, i) => (
                   <div key={i} className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors cursor-pointer group">
                      <div className="flex justify-between items-center">
                         <span className="text-[10px] font-black tracking-widest text-[#22c55e]">{m.symbol}</span>
                         <span className={cn("text-[8px] font-bold px-1.5 py-0.5 rounded", m.regularMarketChangePercent?.raw >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400")}>
                           {m.regularMarketChangePercent?.raw?.toFixed(2)}%
                         </span>
                      </div>
                      <h4 className="text-[10px] font-bold text-white/60 mt-1 truncate">{m.shortName}</h4>
                   </div>
                ))}
              </div>
           </div>

           {/* Section 3: Geopolitical Risk */}
           <div className="space-y-4">
              <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-[0.3em] text-white/20 px-2">
                 <span>Risk Detection</span>
                 <Shield className="w-3 h-3 text-purple-400" />
              </div>
              <div className="space-y-2">
                {geoAlerts.map((g, i) => (
                   <div key={i} className="flex gap-4 p-3 rounded-xl bg-white/[0.01] hover:bg-white/[0.03] transition-colors group">
                      <div className="w-1 h-8 bg-purple-500/40 rounded-full group-hover:bg-purple-500 transition-all" />
                      <div>
                        <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest block mb-1">{g.source}</span>
                        <h4 className="text-[10px] font-bold text-white/50 leading-tight line-clamp-2">{g.title}</h4>
                      </div>
                   </div>
                ))}
              </div>
           </div>

           {/* Section 4: History */}
           <div className="space-y-4 pb-8 border-t border-white/5 pt-8">
              <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-[0.3em] text-white/20 px-2">
                 <span>Neural History</span>
                 <Clock className="w-3 h-3" />
              </div>
              <div className="space-y-1">
                {conversations.map((conv) => (
                  <button 
                    key={conv.id} onClick={() => setActiveConversation(conv.id)}
                    className={cn(
                      "w-full p-4 text-left rounded-2xl border transition-all flex items-center gap-4 group",
                      activeConversation === conv.id ? "bg-[var(--accent)]/[0.05] border-[var(--accent)]/30" : "bg-transparent border-transparent hover:bg-white/5"
                    )}
                  >
                    <MessageSquare className={cn("w-4 h-4 shrink-0 transition-colors", activeConversation === conv.id ? "text-[var(--accent)]" : "text-white/20")} />
                    <div className="flex-1 min-w-0">
                      <span className={cn("text-[10px] font-bold block truncate tracking-tight", activeConversation === conv.id ? "text-white" : "text-white/40")}>{conv.title}</span>
                    </div>
                  </button>
                ))}
              </div>
           </div>
        </div>
      </aside>

      {/* MAIN CHAT INTERFACE */}
      <main className="flex-1 flex flex-col relative z-10 transition-all duration-500">
         {/* Header */}
         <header className="h-20 border-b border-white/5 px-8 flex items-center justify-between bg-[#090B10]/60 backdrop-blur-xl">
            <div className="flex items-center gap-6">
               <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:border-[var(--accent)]/30 text-white/40 hover:text-white transition-all">
                  <Layout className="w-4 h-4" />
               </button>
               <div>
                  <div className="flex items-center gap-2 mb-0.5">
                     <BrainCircuit className="w-4 h-4 text-[var(--accent)]" />
                     <span className="text-[9px] font-black uppercase tracking-[0.5em] text-[var(--accent)]">Analytical Uplink</span>
                  </div>
                  <h1 className="text-xl font-black uppercase tracking-tighter italic">Ontology Specialist</h1>
               </div>
            </div>

            <div className="flex items-center gap-6">
               <div className="flex flex-col items-end">
                  <span className="text-[10px] font-black text-white/60 tracking-wider">Llama 3.3 70B</span>
                  <span className="text-[8px] font-mono text-white/20 uppercase tracking-[0.3em]">Precision :: Neural_Handshake</span>
               </div>
               <div className="h-10 w-px bg-white/5" />
               <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_#34d399]" />
               </div>
            </div>
         </header>

         {/* Feed */}
         <div className="flex-1 overflow-y-auto p-12 space-y-12 custom-scrollbar relative">
            <AnimatePresence>
               {messages.length === 0 ? (
                 <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col items-center justify-center space-y-10 opacity-10 py-20 pointer-events-none">
                    <Cpu className="w-32 h-32" />
                    <div className="text-center space-y-4">
                       <h2 className="text-2xl font-black uppercase tracking-[0.5em]">Input Determinant</h2>
                       <p className="text-sm font-black uppercase tracking-widest max-w-sm mx-auto leading-relaxed">Neural Specialist Awaiting Parameters for Market-Scale Ontology Synthesis.</p>
                    </div>
                 </motion.div>
               ) : (
                 messages.map((m, i) => (
                   <motion.div 
                     key={m.id} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
                     className={cn("flex gap-8 group", m.role === 'user' ? "flex-row-reverse" : "flex-row")}
                   >
                     <div className={cn(
                       "w-12 h-12 rounded-2xl flex items-center justify-center border font-black text-sm relative",
                       m.role === 'user' ? "bg-white/5 border-white/10 text-white/20 italic" : "bg-[var(--accent)]/10 border-[var(--accent)]/20 text-[var(--accent)] shadow-[0_0_20px_rgba(var(--accent-rgb),0.1)]"
                     )}>
                        {m.role === 'user' ? 'U' : <Bot className="w-5 h-5" />}
                        {m.role === 'assistant' && (
                           <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-[var(--online)] rounded-full border-2 border-[#090B10]" />
                        )}
                     </div>

                     <div className={cn(
                       "max-w-[80%] p-8 rounded-[2.5rem] text-sm leading-relaxed relative",
                       m.role === 'user' ? "bg-white/[0.03] text-white/80 rounded-tr-none border border-white/5" : "bg-[#0B0D14]/80 border border-white/5 backdrop-blur-xl text-white/60 rounded-tl-none prose prose-invert prose-sm"
                     )}>
                        {m.role === 'user' ? m.content : <ReactMarkdown>{m.content}</ReactMarkdown>}
                        
                        {m.sources && m.sources.length > 0 && (
                          <div className="mt-8 pt-8 border-t border-white/5 flex flex-wrap gap-3">
                             {m.sources.map((s, idx) => (
                               <a key={idx} href={s.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 px-3 py-1.5 bg-white/[0.02] border border-white/5 rounded-lg hover:bg-white/5 transition-all group/src">
                                  <Globe className="w-3 h-3 text-blue-400 group-hover/src:scale-110" />
                                  <span className="text-[9px] font-bold text-white/30 truncate max-w-[150px] uppercase tracking-tighter">{s.title}</span>
                               </a>
                             ))}
                          </div>
                        )}
                        
                        <div className={cn("absolute top-4 font-mono text-[8px] text-white/10 uppercase tracking-widest", m.role === 'user' ? "-left-12 opacity-0 group-hover:opacity-100" : "-right-12 opacity-0 group-hover:opacity-100")}>
                           {m.timestamp.toLocaleTimeString()}
                        </div>
                     </div>
                   </motion.div>
                 ))
               )}
               {loading && (
                 <div className="flex gap-8">
                    <div className="w-12 h-12 rounded-2xl bg-[var(--accent)]/10 border border-[var(--accent)]/20 flex items-center justify-center">
                       <Loader2 className="w-5 h-5 text-[var(--accent)] animate-spin" />
                    </div>
                    <div className="flex gap-3 items-center px-8 italic text-[10px] text-white/20 uppercase tracking-[0.3em]">
                       <span className="animate-pulse">Synthesizing Neural Layers...</span>
                    </div>
                 </div>
               )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
         </div>

         {/* Bottom Action Area */}
         <div className="p-8 pb-12 bg-gradient-to-t from-[#07080C] via-[#07080C] to-transparent">
            <div className="max-w-5xl mx-auto relative group">
               <div className="absolute -inset-1 bg-gradient-to-r from-[var(--accent)]/20 to-purple-500/20 rounded-[2rem] blur-xl opacity-0 group-focus-within:opacity-100 transition duration-1000" />
               <div className="relative bg-[#0D0F14] border border-white/10 rounded-[2rem] p-4 flex items-end gap-4 shadow-2xl overflow-hidden backdrop-blur-xl group-focus-within:border-[var(--accent)]/40 transition-all">
                  <textarea 
                    ref={textareaRef} value={inputValue} onChange={e => setInputValue(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSubmit())}
                    placeholder="ENTER PARAMETERS FOR MARKET ONTOLOGY ANALYSIS..."
                    className="flex-1 bg-transparent border-none outline-none p-4 text-xs font-bold text-white placeholder:text-white/15 resize-none max-h-[300px] custom-scrollbar uppercase tracking-tight"
                    rows={1}
                  />
                  <div className="flex items-center gap-3 pb-2 pr-2">
                     <button className="p-3 bg-white/5 rounded-2xl border border-white/5 text-white/20 hover:text-white transition-all"><BarChart3 className="w-4 h-4" /></button>
                     <button 
                       onClick={handleSubmit} disabled={!inputValue.trim() || loading}
                       className="w-14 h-14 bg-[var(--accent)] text-[#07080C] rounded-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all shadow-[0_0_30px_rgba(var(--accent-rgb),0.3)] disabled:opacity-20 disabled:scale-100"
                     >
                       {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                     </button>
                  </div>
               </div>
               
               <div className="mt-4 flex items-center justify-center gap-8 opacity-20 hover:opacity-100 transition-opacity">
                  <div className="flex items-center gap-2">
                     <Globe className="w-3 h-3" />
                     <span className="text-[8px] font-black uppercase tracking-widest">Web Research Connected</span>
                  </div>
                  <div className="flex items-center gap-2">
                     <Database className="w-3 h-3" />
                     <span className="text-[8px] font-black uppercase tracking-widest">Knowledge Graph Sync</span>
                  </div>
                  <div className="flex items-center gap-2 text-[var(--accent)]">
                     <Sparkles className="w-3 h-3" />
                     <span className="text-[8px] font-black uppercase tracking-widest italic tracking-tighter">Model: Llama Specialist Free</span>
                  </div>
               </div>
            </div>
         </div>
      </main>
    </div>
  );
}
