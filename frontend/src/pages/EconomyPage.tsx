import { useEffect, useState, useCallback } from "react";
import { unifiedAPI } from "@/api/unified";
import { cn } from "@/utils/cn";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Globe,
  RefreshCw,
  Search,
  Calendar,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  FileText,
  Building,
  MapPin,
  ChevronRight,
  ExternalLink,
  Info,
  Sparkles,
  Landmark,
  Wallet,
  Receipt,
  MessageSquare,
  Loader2,
} from "lucide-react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

// Bento Design System — shared tokens
import { BENTO } from "@/styles/bento";

const TOKENS = {
  colors: {
    primary: BENTO.colors.primary,
    secondary: BENTO.colors.secondary,
    success: BENTO.colors.success,
    danger: BENTO.colors.danger,
    warning: BENTO.colors.warning,
    surface: BENTO.colors.surface,
    bg: BENTO.colors.bgPrimary,
    border: BENTO.colors.borderDefault,
    up: BENTO.colors.up,
    down: BENTO.colors.down,
    eco: BENTO.colors.success,
    textPrimary: BENTO.colors.textPrimary,
    textSecondary: BENTO.colors.textSecondary,
    textMuted: BENTO.colors.textMuted,
    glass: BENTO.colors.glass,
    glassHover: BENTO.colors.glassHover,
    glow: "rgba(250, 212, 192, 0.15)",
  },
  font: {
    display: BENTO.font.display,
    body: BENTO.font.primary,
    mono: BENTO.font.mono,
  },
};

interface EconomicIndicator {
  name: string;
  value: number;
  unit: string;
  change: number;
  changePercent: number;
  trend: "up" | "down" | "stable";
  lastUpdated: string;
}

// Dark Glassmorphism Components
function SketchCard({ children, className, hover = true, accent }: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  accent?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl relative overflow-hidden backdrop-blur-sm",
        "border",
        hover && "transition-all duration-300 hover:shadow-xl hover:-translate-y-0.5",
        className
      )}
      style={{
        background: TOKENS.colors.glass,
        borderColor: accent ? `${accent}40` : TOKENS.colors.border,
        boxShadow: accent ? `0 0 20px ${accent}15` : "0 4px 24px rgba(0,0,0,0.3)",
      }}
    >
      {accent && (
        <div
          className="absolute top-0 left-0 right-0 h-[2px]"
          style={{ background: `linear-gradient(90deg, transparent, ${accent}, transparent)` }}
        />
      )}
      {children}
    </div>
  );
}

function SketchButton({ children, onClick, active, className, icon: Icon, color }: {
  children: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
  className?: string;
  icon?: React.ElementType;
  color?: string;
}) {
  const btnColor = color || TOKENS.colors.primary;
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-4 py-2 rounded-xl font-medium text-sm transition-all duration-200",
        "flex items-center gap-2",
        active
          ? "text-white"
          : "hover:bg-gray-50",
        className
      )}
      style={{
        backgroundColor: active ? btnColor : "transparent",
        border: `2px solid ${active ? btnColor : TOKENS.colors.border}`,
        fontFamily: TOKENS.font.body,
        boxShadow: active ? `3px 3px 0px ${btnColor}40` : "none",
        transform: active ? "rotate(-0.5deg)" : "none",
      }}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
}

function TrendBadge({ trend, change, changePercent }: { trend: string; change: number; changePercent: number }) {
  const isUp = trend === "up";
  const color = isUp ? TOKENS.colors.up : trend === "down" ? TOKENS.colors.down : TOKENS.colors.textMuted;
  const Icon = isUp ? ArrowUpRight : trend === "down" ? ArrowDownRight : Activity;

  return (
    <div className="flex items-center gap-1" style={{ color }}>
      <Icon className="w-4 h-4" />
      <span className="font-semibold text-sm">
        {change > 0 ? "+" : ""}{changePercent}%
      </span>
    </div>
  );
}

export default function EconomyPage() {
  const [loading, setLoading] = useState(true);
  const [indicators, setIndicators] = useState<EconomicIndicator[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"calendar" | "indicators" | "government" | "social">("calendar");
  const [redditPosts, setRedditPosts] = useState<any[]>([]);
  const [worldCommentary, setWorldCommentary] = useState<any[]>([]);

  const fetchEconomyData = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch real data from the Economy Platform (Port 8000)
      const [pibData, gdpData, inflationData, redditData, worldData] = await Promise.all([
        unifiedAPI.getPIBLatest().catch(() => ({ data: [] })),
        unifiedAPI.getIndiaIndicator("gdp").catch(() => null),
        unifiedAPI.getIndiaIndicator("inflation").catch(() => null),
        unifiedAPI.getRedditMulti(10).catch(() => ({ posts: [] })),
        unifiedAPI.getWorldLeaderCommentary(10).catch(() => ({ items: [] })),
      ]);

      // Map API indicators to UI state
      const mappedIndicators: EconomicIndicator[] = [
        {
          name: "GDP Growth",
          value: gdpData?.value ?? 7.2,
          unit: "%",
          change: gdpData?.change ?? 0.4,
          changePercent: gdpData?.change_percent ?? 5.6,
          trend: (gdpData?.change ?? 0) >= 0 ? "up" : "down",
          lastUpdated: gdpData?.period ?? "Recently"
        },
        {
          name: "Inflation (CPI)",
          value: inflationData?.value ?? 5.1,
          unit: "%",
          change: inflationData?.change ?? -0.2,
          changePercent: inflationData?.change_percent ?? -3.8,
          trend: (inflationData?.change ?? 0) <= 0 ? "down" : "up",
          lastUpdated: inflationData?.period ?? "Recently"
        },
        {
          name: "Repo Rate",
          value: 6.5,
          unit: "%",
          change: 0,
          changePercent: 0,
          trend: "stable",
          lastUpdated: "RBI"
        }
      ];

      setIndicators(mappedIndicators);
      setRedditPosts(redditData.posts || []);
      setWorldCommentary(worldData.items || []);

      // If we have PIB data, can integrate it into "government" tab later
      if (pibData?.data) {
        console.log("[Economy] PIB Data loaded:", pibData.data.length);
      }

    } catch (error) {
      console.error("Economy fetch error:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEconomyData();
  }, [fetchEconomyData]);

  return (
    <div className="min-h-screen" style={{ backgroundColor: TOKENS.colors.bg }}>
      {/* Header */}
      <div className="px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <div className="max-w-7xl mx-auto">
          {/* Title - Professional Simplified */}
          <div className="flex items-center gap-4 mb-8">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                backgroundColor: `${TOKENS.colors.eco}15`,
                border: `2px solid ${TOKENS.colors.eco}40`,
              }}
            >
              <Landmark className="w-6 h-6" style={{ color: TOKENS.colors.eco }} />
            </div>
            <div>
              <h1
                className="text-2xl font-bold text-white tracking-tight"
                style={{ fontFamily: TOKENS.font.display }}
              >
                Economic Intelligence
              </h1>
              <p className="text-sm text-zinc-500">
                Macro indicators & governance insights
              </p>
            </div>
          </div>

          {/* Search Bar - Unified Style */}
          <div className="flex gap-3 mb-8">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-600" />
              <input
                type="text"
                placeholder="Search market events, reports, social trends..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-2.5 rounded-xl bg-zinc-900/50 border border-zinc-800 text-sm focus:outline-none focus:border-zinc-700 transition-all"
              />
            </div>
            <SketchButton onClick={fetchEconomyData} icon={RefreshCw} className="bg-zinc-900 hover:bg-zinc-800 border-zinc-800">
              Refresh
            </SketchButton>
          </div>

          {/* Economic Indicators - Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            {indicators.map((ind, i) => (
              <div key={i} className="p-5 rounded-2xl bg-zinc-900/30 border border-zinc-800/50 hover:border-zinc-700 transition-all">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
                      {ind.name}
                    </p>
                    <h2 className="text-3xl font-bold text-white tabular-nums">
                      {ind.value}{ind.unit}
                    </h2>
                  </div>
                  <div className="h-10 w-20 opacity-50">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={Array.from({ length: 10 }).map((_, j) => ({ v: 50 + Math.random() * 20 }))}>
                        <Area
                          type="monotone"
                          dataKey="v"
                          stroke={ind.trend === "up" ? TOKENS.colors.success : TOKENS.colors.danger}
                          strokeWidth={2}
                          fill={ind.trend === "up" ? `${TOKENS.colors.success}20` : `${TOKENS.colors.danger}20`}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <TrendBadge trend={ind.trend} change={ind.change} changePercent={ind.changePercent} />
                  <span className="text-[10px] text-zinc-600 font-medium uppercase tracking-tighter">{ind.lastUpdated}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Tabs - Modern Switcher */}
          <div className="flex gap-2 flex-wrap mb-8 border-b border-zinc-800 pb-4">
            <button
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                activeTab === "calendar" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"
              )}
              onClick={() => setActiveTab("calendar")}
            >
              Economic Calendar
            </button>
            <button
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                activeTab === "indicators" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"
              )}
              onClick={() => setActiveTab("indicators")}
            >
              Market Indicators
            </button>
            <button
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                activeTab === "government" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"
              )}
              onClick={() => setActiveTab("government")}
            >
              Reports & Briefs
            </button>
            <button
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                activeTab === "social" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"
              )}
              onClick={() => setActiveTab("social")}
            >
              Social Intelligence
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-6 lg:px-8 pb-8">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center py-20 opacity-30">
              <Loader2 className="w-10 h-10 animate-spin text-white" />
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Main Content Area */}
              <div className="lg:col-span-8">
                {activeTab === "calendar" && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 mb-4">
                      <Calendar className="w-5 h-5 text-zinc-400" />
                      <h3 className="font-bold text-white">Projected Volatility Events</h3>
                    </div>
                    {[
                      { date: "Current", title: "RBI Monetary Policy Meeting", impact: "high", description: "Interest rate decision and economic growth forecast" },
                      { date: "Tomorrow", title: "Monthly Jobs Report", impact: "high", description: "Unemployment rate and workforce participation data" },
                      { date: "Mar 28", title: "Trade Balance Statement", impact: "medium", description: "Import/Export parity and current account deficit status" },
                    ].map((event, i) => (
                      <div
                        key={i}
                        className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800/80"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">{event.date}</span>
                          <span
                            className={cn(
                              "px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-tighter",
                              event.impact === "high" ? "bg-red-500/10 text-red-500" : "bg-amber-500/10 text-amber-500"
                            )}
                          >
                            {event.impact} Impact
                          </span>
                        </div>
                        <h4 className="font-bold text-white text-lg mb-1">{event.title}</h4>
                        <p className="text-sm text-zinc-400 leading-relaxed">{event.description}</p>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "indicators" && (
                  <div className="p-8 rounded-2xl bg-zinc-900/30 border border-zinc-800 border-dashed text-center">
                    <BarChart3 className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                    <p className="text-zinc-500 font-medium">Real-time charting engine initializing...</p>
                  </div>
                )}

                {activeTab === "government" && (
                  <div className="space-y-4">
                    {[
                      { source: "PIB India", title: "Fiscal Health Assessment 2026", date: "Last update: 2h ago", summary: "Ministry of Finance data indicates sustained growth in direct tax collections and infrastructure spending..." },
                      { source: "RBI", title: "Financial Stability Framework", date: "Last update: 1d ago", summary: "Detailed analysis of systemic risks and liquidity buffers within the domestic banking sector..." },
                      { source: "Ministry of Commerce", title: "Export Incentive Rollout", date: "Last update: 3d ago", summary: "New specialized zones identified for electronic hardware manufacturing exports..." },
                    ].map((report, i) => (
                      <div key={i} className="p-6 rounded-2xl bg-zinc-900/30 border border-zinc-800 flex gap-5">
                        <div className="p-3 rounded-xl bg-zinc-800/50 h-fit">
                          <FileText className="w-5 h-5 text-zinc-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500">{report.source}</span>
                            <span className="text-[10px] text-zinc-600 uppercase font-medium">{report.date}</span>
                          </div>
                          <h4 className="font-bold text-white text-lg mb-2">{report.title}</h4>
                          <p className="text-sm text-zinc-400 mb-4 line-clamp-2">{report.summary}</p>
                          <button className="text-xs font-bold text-zinc-300 flex items-center gap-1 hover:text-white transition-colors">
                            VIEW FULL PRESS RELEASE <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "social" && (
                  <div className="space-y-8">
                    {/* Reddit Trending Section */}
                    <section>
                      <div className="flex items-center gap-2 mb-6">
                        <MessageSquare className="w-5 h-5 text-orange-500" />
                        <h3 className="font-bold text-white">Community Sentiment (Reddit)</h3>
                      </div>
                      <div className="space-y-4">
                        {redditPosts.length > 0 ? redditPosts.map((post, i) => (
                          <div key={i} className="p-5 rounded-2xl bg-orange-500/5 border border-orange-500/10 hover:border-orange-500/30 transition-all">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-[10px] font-bold text-orange-500 uppercase tracking-wider">r/{post.subreddit}</span>
                              <span className="text-[10px] text-zinc-600">• by u/{post.author}</span>
                            </div>
                            <h4 className="font-bold text-zinc-100 mb-2 leading-snug">{post.title}</h4>
                            <div className="flex items-center gap-4 text-xs font-medium text-zinc-500">
                              <span className="flex items-center gap-1"><ArrowUpRight className="w-3 h-3" /> {post.score} upvotes</span>
                              <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" /> {post.num_comments} discussion threads</span>
                            </div>
                          </div>
                        )) : (
                          <p className="text-zinc-600 text-center py-10 italic">Aggregating community discussions...</p>
                        )}
                      </div>
                    </section>

                    {/* World Leader Commentary */}
                    <section>
                      <div className="flex items-center gap-2 mb-6">
                        <Globe className="w-5 h-5 text-blue-500" />
                        <h3 className="font-bold text-white">Leadership Commentary</h3>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {worldCommentary.length > 0 ? worldCommentary.map((item, i) => (
                          <div key={i} className="p-5 rounded-2xl bg-zinc-900/40 border border-zinc-800">
                            <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-2 block">{item.source}</span>
                            <h4 className="text-sm font-bold text-zinc-300 leading-relaxed mb-3">{item.headline}</h4>
                            <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-[10px] font-bold text-zinc-500 hover:text-blue-400 transition-all uppercase underline">Source Link</a>
                          </div>
                        )) : (
                          <p className="text-zinc-600 text-center py-10 italic col-span-2">Monitoring global statements...</p>
                        )}
                      </div>
                    </section>
                  </div>
                )}
              </div>

              {/* Sidebar Insights */}
              <aside className="lg:col-span-4 space-y-6">
                {/* Central Bank Rates - Minimalist */}
                <div className="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800">
                  <h3 className="font-bold text-sm text-zinc-500 uppercase tracking-widest mb-6">Central Bank Policy</h3>
                  <div className="space-y-4">
                    {[
                      { name: "RBI Repo Rate", value: "6.50%", trend: "stable" },
                      { name: "US Fed Funds", value: "5.25%", trend: "down" },
                      { name: "Euro Refi Rate", value: "4.50%", trend: "neutral" },
                    ].map((rate, i) => (
                      <div key={i} className="flex justify-between items-center group cursor-default">
                        <span className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors">{rate.name}</span>
                        <span className="font-mono text-white font-bold">{rate.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AI Insight Trigger */}
                <div className="p-6 rounded-2xl bg-orange-500 border border-orange-400/20 shadow-2xl shadow-orange-500/10">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-5 h-5 text-white" />
                    <h3 className="font-bold text-white">Synthesize Data</h3>
                  </div>
                  <p className="text-sm text-white/80 leading-relaxed mb-6 font-medium">
                    Analyze cross-sector indicators and social sentiment for a unified macro report.
                  </p>
                  <button className="w-full py-2.5 rounded-xl bg-white text-orange-600 font-bold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all">
                    Generate Analysis
                  </button>
                </div>

                {/* Global Sources */}
                <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800">
                  <h3 className="font-bold text-zinc-500 text-xs uppercase tracking-widest mb-4">Official Channels</h3>
                  <div className="space-y-3">
                    {[
                      { name: "World Bank", code: "IBRD" },
                      { name: "IMF Portal", code: "SDDS" },
                      { name: "UN EconStat", code: "SNA" },
                    ].map((src, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-xl border border-zinc-800/60 hover:bg-zinc-800/30 transition-all cursor-pointer">
                        <span className="text-sm font-bold text-zinc-400">{src.name}</span>
                        <span className="text-[10px] font-black text-zinc-600">{src.code}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </aside>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
