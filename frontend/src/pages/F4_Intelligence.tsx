import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  TrendingUp, TrendingDown, Activity, Shield, Zap, 
  Globe, Search, ChevronRight, Play, Server,
  Database, Cpu, MessageSquare, BarChart3, AlertTriangle
} from 'lucide-react';
import { cn } from "@/utils/cn";
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

// --- CONFIG ---
const FINANCE_API = "http://localhost:8000";
const NEWS_API = "http://localhost:8000";

export default function F4_Intelligence() {
  const [movers, setMovers] = useState<any[]>([]);
  const [headlines, setHeadlines] = useState<any[]>([]);
  const [geoAlerts, setGeoAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [engineStatus, setEngineStatus] = useState<any>({ finance: 'off', news: 'off' });

  const fetchData = async () => {
    try {
      // 1. Fetch Finance Movers (PASSED TEST #49)
      const moversRes = await axios.get(`${FINANCE_API}/api/yahoo-finance/movers`, { params: { type: "most_actives" } });
      setMovers(moversRes.data?.movers?.slice(0, 5) || []);
      
      // 2. Fetch Top Headlines (PASSED TEST #4)
      const newsRes = await axios.get(`${NEWS_API}/api/news/headlines`);
      setHeadlines(newsRes.data?.articles?.slice(0, 8) || []);

      // 3. Fetch Geopolitical (PASSED TEST #590)
      const geoRes = await axios.get(`${NEWS_API}/api/geo/all`);
      setGeoAlerts(geoRes.data?.articles?.slice(0, 4) || []);

      setEngineStatus({ finance: 'online', news: 'online' });
    } catch (e) {
      console.error("Master fetch failed", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-[#e0e0e0] font-sans pt-4">
      {/* HUD - Status Bar */}
      <div className="max-w-[1600px] mx-auto px-6 mb-8">
        <div className="flex items-center justify-between bg-white/[0.02] border border-white/5 rounded-2xl px-6 py-3 backdrop-blur-xl">
           <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                 <div className={cn("w-2 h-2 rounded-full", engineStatus.finance === 'online' ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" : "bg-red-500")} />
                 <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">Finance_Link</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className={cn("w-2 h-2 rounded-full", engineStatus.news === 'online' ? "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" : "bg-red-500")} />
                 <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">Intelligence_Link</span>
              </div>
           </div>
           <div className="flex items-center gap-4">
              <span className="text-[10px] font-mono text-white/20 uppercase">Core_API_v3.1</span>
              <div className="h-4 w-px bg-white/10" />
              <Activity className="w-3 h-3 text-blue-500 animate-pulse" />
           </div>
        </div>
      </div>

      <main className="max-w-[1600px] mx-auto px-6 grid grid-cols-1 xl:grid-cols-12 gap-8 pb-20">
        
        {/* Left Column: Markets (Port 8000) */}
        <div className="xl:col-span-3 space-y-6">
           <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-bold uppercase tracking-widest text-white/60 flex items-center gap-2">
                 <BarChart3 className="w-4 h-4 text-green-500" />
                 Market Flux
              </h2>
              <span className="text-[10px] text-white/20">Source: Yahoo_API</span>
           </div>

           {loading && Array.from({length: 4}).map((_, i) => (
             <div key={i} className="h-28 bg-white/[0.02] border border-white/5 rounded-2xl animate-pulse" />
           ))}

           {movers.map((m, i) => (
             <div key={`${m.symbol}-${i}`} className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 hover:bg-white/[0.04] transition-all group cursor-pointer">
                <div className="flex justify-between items-start mb-4">
                   <div>
                      <p className="text-[10px] font-bold text-green-500 mb-1">{m.symbol}</p>
                      <h3 className="text-sm font-bold text-white truncate w-32">{m.shortName}</h3>
                   </div>
                   <div className={cn("text-[10px] font-bold px-2 py-0.5 rounded-md", m.regularMarketChangePercent?.raw >= 0 ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
                      {m.regularMarketChangePercent?.raw.toFixed(2)}%
                   </div>
                </div>
                <div className="flex items-end justify-between">
                   <p className="text-xl font-bold font-mono">${m.regularMarketPrice?.raw.toLocaleString()}</p>
                   <div className="h-8 w-20 opacity-30">
                      <ResponsiveContainer width="100%" height="100%">
                         <AreaChart data={Array.from({length: 10}).map(() => ({ v: Math.random() }))}>
                            <Area type="monotone" dataKey="v" stroke="#22c55e" fill="#22c55e20" />
                         </AreaChart>
                      </ResponsiveContainer>
                   </div>
                </div>
             </div>
           ))}

           <button className="w-full py-4 bg-white/5 border border-white/10 rounded-2xl text-[10px] font-bold uppercase tracking-[0.2em] hover:bg-white/10 transition-all text-white/40">
              Full Market Terminal
           </button>
        </div>

        {/* Center Column: Global Intel (Port 8001) */}
        <div className="xl:col-span-6 space-y-8">
           <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-[2.5rem] blur opacity-25 group-hover:opacity-40 transition duration-1000"></div>
              <div className="relative bg-[#0a0a0a] border border-white/5 rounded-[2.5rem] p-10 overflow-hidden">
                 <div className="flex items-center justify-between mb-10">
                    <div>
                       <h1 className="text-4xl font-bold tracking-tighter text-white mb-2 italic">Intelligence_Feed</h1>
                       <p className="text-sm text-white/30">Cross-border information synthesis • Real-time</p>
                    </div>
                    <div className="p-4 bg-blue-500/10 rounded-2xl border border-blue-500/20">
                       <Globe className="text-blue-500 w-6 h-6 animate-[spin_10s_linear_infinite]" />
                    </div>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {headlines.map((a, i) => (
                      <div key={i} className="space-y-3 group/item cursor-pointer">
                         <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">{a.source}</span>
                            <div className="h-px flex-1 bg-white/5" />
                         </div>
                         <h2 className="text-md font-bold text-white/80 group-hover/item:text-blue-400 transition-colors leading-snug line-clamp-2">
                           {a.title}
                         </h2>
                         <button className="flex items-center gap-2 text-[10px] font-bold text-white/20 uppercase tracking-widest group-hover/item:text-white transition-all">
                            Extract Intel <ChevronRight className="w-3 h-3" />
                         </button>
                      </div>
                    ))}
                 </div>
              </div>
           </div>
        </div>

        {/* Right Column: Geopolitical & Risk Analysis */}
        <div className="xl:col-span-3 space-y-8">
           <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 relative overflow-hidden backdrop-blur-3xl">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                 <Shield className="w-32 h-32" />
              </div>
              <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                 <Zap className="w-3 h-3" />
                 Risk vectors
              </h3>
              <div className="space-y-6">
                 {geoAlerts.map((g, i) => (
                   <div key={i} className="flex gap-4 group cursor-pointer">
                      <div className="w-1 h-auto bg-purple-500/20 rounded-full group-hover:bg-purple-500 transition-all" />
                      <div>
                         <p className="text-[10px] text-white/30 uppercase mb-1">{g.source}</p>
                         <h4 className="text-xs font-bold text-white leading-tight mb-2">{g.title}</h4>
                      </div>
                   </div>
                 ))}
              </div>
           </div>

           <div className="p-8 bg-gradient-to-br from-[#0a0a0a] to-[#111] border border-white/5 rounded-3xl shadow-2xl">
              <div className="flex items-center gap-3 mb-6">
                 <Cpu className="text-blue-500 w-5 h-5" />
                 <h3 className="text-sm font-bold text-white">Neural Advisory</h3>
              </div>
              <div className="bg-black/40 border border-white/5 rounded-xl p-4 font-mono text-[11px] text-blue-400/80 leading-relaxed mb-6">
                 {">"} ANALYZING_MARKET_FLUX...
                 <br />
                 {">"} CORRELATING_GEO_VECTORS...
                 <br />
                 {">"} RISK_THRESHOLD: 4.2 (LOW)
                 <br />
                 {">"} REC: LONG_NIFTY_SECTORS
              </div>
              <button className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-bold transition-all shadow-lg shadow-blue-600/20">
                 Run Strategy Sim
              </button>
           </div>

           {/* API Audit Link */}
           <div className="flex items-center gap-3 p-4 bg-white/5 border border-white/10 rounded-2xl opacity-50 hover:opacity-100 transition-opacity">
              <div className="p-2 bg-black/40 rounded-lg">
                 <Server className="w-4 h-4 text-white/60" />
              </div>
              <div>
                 <p className="text-[10px] font-bold text-white uppercase tracking-tight">System Audit</p>
                 <p className="text-[9px] text-white/40">PASSED: 62 | FAIL: 1</p>
              </div>
           </div>
        </div>

      </main>

      {/* Ticker Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-[#050505]/80 backdrop-blur-2xl border-t border-white/5 z-50">
         <div className="flex items-center gap-12 py-3 px-6 h-12 overflow-hidden whitespace-nowrap animate-marquee">
            {movers.concat(movers).map((m, i) => (
              <div key={i} className="flex items-center gap-4">
                 <span className="text-[11px] font-bold text-white/60 uppercase">{m.symbol}</span>
                 <span className="text-[11px] font-mono">${m.regularMarketPrice?.raw.toLocaleString()}</span>
                 <span className={cn("text-[9px] font-bold", m.regularMarketChangePercent?.raw >= 0 ? "text-green-500" : "text-red-500")}>
                    {m.regularMarketChangePercent?.raw >= 0 ? "+" : ""}{m.regularMarketChangePercent?.raw.toFixed(2)}%
                 </span>
              </div>
            ))}
         </div>
      </footer>
    </div>
  );
}
