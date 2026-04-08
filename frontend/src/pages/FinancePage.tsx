import { useState, useEffect, useRef, memo } from "react";
import { motion } from "framer-motion";
import { 
  Search, TrendingUp, Activity, ChevronRight, ChevronDown,
  BarChart3, PieChart, Layers, Globe, Newspaper, 
  Flame, Bitcoin, DollarSign, FileText, Users, Building2, 
  Calendar as CalendarIcon, Shield, Star, MessageSquare,
  Bot, Send, Loader2
} from "lucide-react";
import { cn } from "@/utils/cn";
import LazyWidget from "@/components/finance/LazyWidget";

// ── TradingView Script Widget ────────────────────────────────
const TVWidget = memo(({ scriptSrc, config, height = "500px" }: { scriptSrc: string; config: any; height?: string }) => {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current) return;
    container.current.innerHTML = '';
    const inner = document.createElement('div');
    inner.className = 'tradingview-widget-container__widget';
    container.current.appendChild(inner);
    const script = document.createElement('script');
    script.src = scriptSrc;
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({ ...config, colorTheme: 'dark', isTransparent: true, locale: 'en', width: '100%' });
    container.current.appendChild(script);
    return () => { if (container.current) container.current.innerHTML = ''; };
  }, [scriptSrc, JSON.stringify(config)]);
  return <div ref={container} className="tradingview-widget-container" style={{ height, width: '100%' }} />;
});

// ── TV Advanced Chart ────────────────────────────────────────
const TVAdvancedChart = memo(({ symbol, height = "600px" }: { symbol: string; height?: string }) => {
  const container = useRef<HTMLDivElement>(null);
  const chartId = useRef(`tvchart_${Math.random().toString(36).substr(2,9)}`);
  useEffect(() => {
    if (!container.current) return;
    container.current.innerHTML = '';
    const chartDiv = document.createElement('div');
    chartDiv.id = chartId.current;
    chartDiv.style.height = '100%';
    chartDiv.style.width = '100%';
    container.current.appendChild(chartDiv);
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if ((window as any).TradingView) {
        new (window as any).TradingView.widget({
          autosize: true, symbol: symbol.includes(':') ? symbol : `BSE:${symbol}`, interval: 'D', timezone: 'Asia/Kolkata',
          theme: 'dark', style: '1', locale: 'en', enable_publishing: false,
          allow_symbol_change: true, container_id: chartId.current,
          hide_top_toolbar: false, hide_legend: false, save_image: true,
          backgroundColor: 'rgba(0,0,0,0)', gridLineColor: 'rgba(255,255,255,0.04)',
        });
      }
    };
    document.head.appendChild(script);
  }, [symbol]);
  return <div ref={container} style={{ height, width: '100%' }} />;
});

// ── Section Divider ──────────────────────────────────────────
const SectionDivider = ({ title, icon: Icon, count, color }: { title: string; icon: any; count: number; color: string }) => (
  <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-4 py-6">
    <div className={cn("p-3 rounded-xl border", color)}><Icon className="w-5 h-5" /></div>
    <div className="flex-1"><h2 className="text-xl font-black tracking-tight text-white">{title}</h2></div>
    <span className="px-3 py-1.5 rounded-xl bg-white/5 text-[10px] font-bold text-white/50 font-mono">{count} WIDGETS</span>
  </motion.div>
);

// ── Glass Card for Bento Grid ────────────────────────────────
const GlassCard = memo(({ children, title, icon: Icon, className, span = "1", defaultOpen = true, onSearch }: {
  children: React.ReactNode; title: string; icon: any; className?: string;
  span?: string; defaultOpen?: boolean; onSearch?: (s: string) => void;
}) => {
  const [open, setOpen] = useState(defaultOpen);
  const [localSearch, setLocalSearch] = useState("");
  const colClass = span === "full" ? "col-span-12" : span === "2" ? "col-span-12 lg:col-span-6" : "col-span-12 lg:col-span-6 xl:col-span-4";
  
  return (
    <div className={cn(colClass, "glass-card !rounded-2xl overflow-hidden transition-all duration-300", !open && "!p-0", className)}>
      <div className="w-full flex items-center gap-3 p-4 text-left border-b border-white/5 bg-white/[0.01]">
        <button onClick={() => setOpen(!open)} className="p-1.5 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] hover:scale-110 transition-transform">
          <Icon className="w-3.5 h-3.5" />
        </button>
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/60 flex-1">{title}</span>
        
        {onSearch && open && (
          <div className="flex items-center bg-black/40 border border-white/10 rounded-lg px-2 py-1 mr-2 group focus-within:border-[var(--accent)]/40 transition-all">
            <Search className="w-2.5 h-2.5 text-white/20 group-focus-within:text-[var(--accent)]" />
            <input 
              type="text" 
              placeholder="SEARCH..." 
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === "Enter" && localSearch) {
                  onSearch(localSearch);
                  setLocalSearch("");
                }
              }}
              className="bg-transparent border-none outline-none text-[9px] font-black tracking-widest text-white ml-2 w-20 placeholder:text-white/10"
            />
          </div>
        )}

        <button onClick={() => setOpen(!open)} className="p-1">
          <ChevronDown className={cn("w-3.5 h-3.5 text-white/20 transition-transform", open && "rotate-180")} />
        </button>
      </div>
      {open && <div className="px-1 pb-1">{children}</div>}
    </div>
  );
});

// ══════════════════════════════════════════════════════════════
export default function FinancePage() {
  const [symbol, setSymbol] = useState("BSE:SENSEX");
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (s: string) => {
    if (!s.trim()) return;
    let newSymbol = s.toUpperCase().trim();
    if (!newSymbol.includes(":")) newSymbol = `BSE:${newSymbol}`;
    setSymbol(newSymbol);
    setSearchQuery("");
  };

  return (
    <div className="min-h-screen bg-[#07080C] text-white overflow-hidden selection:bg-[var(--accent)]/30">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-[var(--accent)]/4 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-[var(--secondary)]/4 blur-[150px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-[1800px] mx-auto px-4 md:px-8 py-6 space-y-4 h-screen overflow-y-auto scrollable">

        {/* Header */}
        <div className="glass-card !rounded-2xl !p-5 flex flex-col lg:flex-row items-stretch lg:items-center gap-6">
          <div className="flex items-center gap-5 flex-1">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-[var(--accent)]/20 to-transparent border border-[var(--accent)]/20">
              <Activity className="w-7 h-7 text-[var(--accent)]" />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-tighter">FINANCE <span className="text-[var(--accent)]">TERMINAL</span></h1>
              <p className="text-[9px] uppercase tracking-[0.4em] text-white/25 font-black mt-1">TradingView Advanced Intelligence</p>
            </div>
          </div>
          <form onSubmit={(e) => { e.preventDefault(); handleSearch(searchQuery); }} className="relative w-full lg:w-[380px]">
            <div className="flex items-center bg-[#0D0F14] border border-white/10 rounded-2xl overflow-hidden focus-within:border-[var(--accent)]/40 transition-all">
              <Search className="ml-4 w-4 h-4 text-white/20" />
              <input type="text" placeholder="SYMBOL (BSE:500325, AAPL)" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent px-3 py-3.5 text-xs font-bold tracking-widest placeholder:text-white/15 focus:outline-none uppercase font-mono" />
              <button type="submit" className="mr-2 p-2 rounded-xl hover:bg-white/5 text-white/20 hover:text-[var(--accent)]"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </form>
        </div>

        {/* Ticker Tape */}
        <div className="h-11 glass-card overflow-hidden !rounded-xl !p-0 relative">
          <div className="absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-[#07080C] to-transparent z-10" />
          <div className="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-[#07080C] to-transparent z-10" />
          <TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" height="44px" config={{
            symbols: [
              { proName: "BSE:SENSEX", title: "SENSEX" }, { proName: "NASDAQ:AAPL", title: "APPLE" },
              { proName: "NASDAQ:TSLA", title: "TESLA" }, { proName: "BINANCE:BTCUSDT", title: "BTC" },
              { proName: "FOREXCOM:USDINR", title: "USD/INR" }, { proName: "COMEX:GC1!", title: "GOLD" },
              { proName: "NYMEX:CL1!", title: "CRUDE" }, { proName: "BITSTAMP:ETHUSD", title: "ETH" }
            ], showSymbolLogo: true, displayMode: "adaptive"
          }} />
        </div>

        {/* ═══ TRADINGVIEW ═══ */}
        <SectionDivider title="Intelligence Dashboard" icon={TrendingUp} count={14} color="bg-blue-500/20 border-blue-500/30 text-blue-400" />
        <div className="grid grid-cols-12 gap-4">
          <GlassCard title="Advanced Real-Time Chart" icon={Activity} span="full" defaultOpen={true}>
            <LazyWidget height="600px" placeholder="Loading Chart..."><TVAdvancedChart symbol={symbol} height="600px" /></LazyWidget>
          </GlassCard>
          
          <GlassCard title="Symbol Overview" icon={BarChart3} span="2" onSearch={handleSearch}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" height="440px" config={{
              symbols: [[symbol.split(':')[1]||symbol, symbol]], chartOnly: false, autosize: true, showVolume: true, chartType: "area"
            }} /></LazyWidget>
          </GlassCard>
          
          <GlassCard title="Technical Analysis Gauge" icon={Activity} span="1" onSearch={handleSearch}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" height="440px" config={{ symbol, interval: "1D", showIntervalTabs: true, displayMode: "single" }} /></LazyWidget>
          </GlassCard>
          
          <GlassCard title="Symbol Info" icon={FileText} span="1" onSearch={handleSearch}>
            <LazyWidget height="200px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js" height="200px" config={{ symbol }} /></LazyWidget>
          </GlassCard>
          
          <GlassCard title="Company Profile" icon={Building2} span="1" onSearch={handleSearch}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js" height="440px" config={{ symbol }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Market Hotlists" icon={Flame} span="1">
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" height="440px" config={{ colorTheme: "dark", dateRange: "12M", exchange: "BSE", showChart: true, locale: "en", width: "100%", height: "100%", largeChartUrl: "", isTransparent: true, showSymbolLogo: false, showFloatingTooltip: false, plotLineColorGrowing: "rgba(41, 98, 255, 1)", plotLineColorFalling: "rgba(41, 98, 255, 1)", gridLineColor: "rgba(240, 243, 250, 0)", scaleFontColor: "rgba(209, 212, 220, 1)", belowLineFillColorGrowing: "rgba(41, 98, 255, 0.12)", belowLineFillColorFalling: "rgba(41, 98, 255, 0.12)", belowLineFillColorGrowingBottom: "rgba(41, 98, 255, 0)", belowLineFillColorFallingBottom: "rgba(41, 98, 255, 0)", symbolActiveColor: "rgba(41, 98, 255, 0.12)" }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Fundamental Data" icon={FileText} span="full" defaultOpen={true}>
            <LazyWidget height="800px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" height="800px" config={{ symbol, displayMode: "regular" }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Stock Market Heatmap" icon={PieChart} span="full" defaultOpen={false}>
            <LazyWidget height="600px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" height="600px" config={{ dataSource: "S&P500", groupBy: "sector", hasTopBar: true, isTransparent: true, symbolActiveColor: "rgba(41, 98, 255, 0.12)" }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Forex Heatmap" icon={Globe} span="2" defaultOpen={false}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-forex-heat-map.js" height="440px" config={{ currencies: ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD", "CNY"], isTransparent: true }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Crypto Heatmap" icon={Bitcoin} span="2" defaultOpen={false}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js" height="440px" config={{ dataSource: "Crypto", grouping: "sector", hasTopBar: true, isTransparent: true }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Market Overview" icon={Globe} span="2" defaultOpen={false}>
            <LazyWidget height="440px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" height="440px" config={{
              showChart: true, showSymbolLogo: true, dateRange: "12M",
              tabs: [
                { title: "Indices", symbols: [{ s: "BSE:SENSEX", d: "Sensex" }, { s: "SP:SPX", d: "S&P 500" }, { s: "NASDAQ:NDX", d: "Nasdaq 100" }] },
                { title: "Commodities", symbols: [{ s: "COMEX:GC1!", d: "Gold" }, { s: "NYMEX:CL1!", d: "Crude" }] },
                { title: "Forex", symbols: [{ s: "FX_IDC:USDINR", d: "USD/INR" }, { s: "FX:EURUSD", d: "EUR/USD" }] }
              ]
            }} /></LazyWidget>
          </GlassCard>

          <GlassCard title="Financial News" icon={Newspaper} span="2" defaultOpen={false}>
            <LazyWidget height="520px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" height="520px" config={{ feedMode: "symbol", symbol, displayMode: "regular" }} /></LazyWidget>
          </GlassCard>
          
          <GlassCard title="Economic Calendar" icon={CalendarIcon} span="2" defaultOpen={false}>
            <LazyWidget height="560px"><TVWidget scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-events.js" height="560px" config={{ importanceFilter: "-1,0,1", countryFilter: "in,us,eu" }} /></LazyWidget>
          </GlassCard>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between glass-card !rounded-2xl !p-4 my-6 text-[9px] font-mono font-bold text-white/25 uppercase tracking-[0.3em]">
          <span>AARAMBH V3.0 • SYNCED INTELLIGENCE TERMINAL</span>
          <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[var(--online)]" /> operational</span>
        </div>
      </div>
    </div>
  );
}
