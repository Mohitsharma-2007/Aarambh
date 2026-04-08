import { useEffect, useState, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  PieChart,
  Globe,
  RefreshCw,
  Search,
  Calendar,
  Clock,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  Activity,
  FileText,
  Building,
  MapPin,
  ChevronRight,
  ExternalLink,
  Menu,
  Bell,
  Settings,
  MoreVertical,
} from "lucide-react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip as ReTooltip
} from "recharts";
import { cn } from "@/utils/cn";
import { EconomyAPI } from "@/api/client";

interface EconomicEvent {
  id: string;
  date: string;
  title: string;
  description: string;
  impact: "high" | "medium" | "low";
  actual?: string;
  forecast?: string;
  previous?: string;
  source: string;
}

interface EconomicIndicator {
  name: string;
  value: number;
  unit: string;
  change: number;
  changePercent: number;
  trend: "up" | "down" | "stable";
  lastUpdated: string;
}

interface GovernmentData {
  title: string;
  description: string;
  value: string;
  source: string;
  date: string;
}

export default function Economy() {
  const [loading, setLoading] = useState(true);
  const [economicEvents, setEconomicEvents] = useState<EconomicEvent[]>([]);
  const [indicators, setIndicators] = useState<EconomicIndicator[]>([]);
  const [governmentData, setGovernmentData] = useState<GovernmentData[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"calendar" | "indicators" | "government">("calendar");

  const fetchEconomyData = useCallback(async () => {
    try {
      setLoading(true);
      const [calendarData, gdpData, inflationData, pibData, ndapData] = await Promise.all([
        EconomyAPI.getEconomicCalendar().catch(() => []),
        EconomyAPI.getIndiaIndicator("gdp").catch(() => null),
        EconomyAPI.getIndiaIndicator("inflation").catch(() => null),
        EconomyAPI.getPIBLatest().catch(() => []),
        EconomyAPI.getNDAPData("employment").catch(() => []),
      ]);

      // Process calendar
      const calendarList: any[] = Array.isArray(calendarData) ? calendarData : (calendarData?.events || []);
      setEconomicEvents(calendarList.slice(0, 15));

      // Process indicators
      const extract = (raw: any) => ({
        value: parseFloat(raw?.value || 0),
        change: parseFloat(raw?.change || 0),
        changePercent: parseFloat(raw?.changePercent || 0)
      });

      const gdp = extract(gdpData);
      const infl = extract(inflationData);

      setIndicators([
        {
          name: "GDP Growth",
          value: gdp.value || 7.2,
          unit: "%",
          change: 0.4,
          changePercent: 5.6,
          trend: "up",
          lastUpdated: "Recently"
        },
        {
          name: "Inflation (CPI)",
          value: infl.value || 5.1,
          unit: "%",
          change: -0.2,
          changePercent: -3.8,
          trend: "down",
          lastUpdated: "Recently"
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
      ]);

      // Process government
      const pib = (pibData?.articles || pibData || []).slice(0, 5).map((item: any) => ({
        title: "PIB Release",
        description: item.title || "Government Update",
        value: item.summary || "Latest release content available in full report.",
        source: "PIB India",
        date: item.date || new Date().toISOString()
      }));
      setGovernmentData(pib);

    } catch (error) {
      console.error("Economy fetch error:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEconomyData();
  }, [fetchEconomyData]);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high": return "bg-[#fce8e6] text-[#c5221f]";
      case "medium": return "bg-[#fef7e0] text-[#b06000]";
      case "low": return "bg-[#e6f4ea] text-[#137333]";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex flex-col font-sans text-[#3c4043]">
      <header className="sticky top-0 z-50 bg-white border-b border-[#dadce0]">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#5f6368]"><Menu className="w-6 h-6" /></button>
            <h1 className="text-xl font-medium tracking-tight text-[#5f6368] flex items-center gap-2">
              <Globe className="w-6 h-6 text-[#1a73e8]" />
              Economy <span className="text-sm font-normal text-[#5f6368] hidden md:inline">Dashboard</span>
            </h1>
          </div>

          <div className="flex-1 max-w-[640px] mx-8 hidden md:block">
            <div className="flex items-center bg-[#f1f3f4] rounded-full px-5 py-2">
              <Search className="w-5 h-5 text-[#5f6368]" />
              <input
                type="text"
                placeholder="Search indicators, events, reports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent ml-3 outline-none text-sm placeholder:text-[#5f6368]"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={fetchEconomyData} className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#5f6368]">
              <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
            </button>
            <button className="p-2 hover:bg-[#f1f3f4] rounded-full text-[#5f6368]"><Settings className="w-5 h-5" /></button>
            <div className="w-8 h-8 bg-[#34a853] rounded-full flex items-center justify-center text-white text-xs font-bold ml-2">E</div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-8">
        {/* Rapid Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {indicators.map((ind, i) => (
            <div key={i} className="bg-white rounded-xl border border-[#dadce0] p-6 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
              <div>
                <p className="text-sm text-[#5f6368] mb-1">{ind.name}</p>
                <div className="flex items-baseline gap-2">
                  <h2 className="text-3xl font-normal text-[#202124]">{ind.value}{ind.unit}</h2>
                  <span className={cn("text-sm font-medium flex items-center", ind.trend === 'up' ? "text-[#137333]" : "text-[#c5221f]")}>
                    {ind.trend === 'up' ? '+' : ''}{ind.changePercent}%
                  </span>
                </div>
              </div>
              <div className="h-12 w-24">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={Array.from({ length: 10 }).map((_, j) => ({ v: 50 + Math.random() * 20 }))}>
                    <Area type="monotone" dataKey="v" stroke={ind.trend === 'up' ? '#137333' : '#c5221f'} fill={ind.trend === 'up' ? '#e6f4ea' : '#fce8e6'} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-1 mb-6 border-b border-[#dadce0]">
          {[
            { id: "calendar", label: "Economic Calendar", icon: Calendar },
            { id: "indicators", label: "Market Indicators", icon: Activity },
            { id: "government", label: "Latest Reports", icon: FileText }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "px-6 py-4 text-sm font-medium border-b-2 flex items-center gap-2 transition-all",
                activeTab === tab.id
                  ? "border-[#1a73e8] text-[#1a73e8]"
                  : "border-transparent text-[#5f6368] hover:bg-white"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-[#dadce0]">
            <RefreshCw className="w-10 h-10 text-[#1a73e8] animate-spin mb-4" />
            <p className="text-[#5f6368]">Aggregating economic data from 12+ sources...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8">
              {activeTab === "calendar" && (
                <section className="bg-white rounded-xl border border-[#dadce0] overflow-hidden shadow-sm">
                  <div className="px-6 py-4 border-b border-[#dadce0] flex items-center justify-between">
                    <h3 className="font-medium text-[#202124]">Upcoming Economic Events</h3>
                    <span className="text-xs text-[#1a73e8] hover:underline cursor-pointer">View full calendar</span>
                  </div>
                  <div className="divide-y divide-[#dadce0]">
                    {economicEvents.map((event, i) => (
                      <div key={i} className="p-6 hover:bg-[#f8f9fa] transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase", getImpactColor(event.impact))}>
                              {event.impact}
                            </span>
                            <span className="text-xs text-[#5f6368] font-medium">{event.date}</span>
                          </div>
                          <span className="text-[10px] text-[#9aa0a6]">{event.source}</span>
                        </div>
                        <h4 className="text-[15px] font-medium text-[#202124] mb-1">{event.title}</h4>
                        <p className="text-sm text-[#5f6368] mb-4">{event.description}</p>

                        {event.actual && (
                          <div className="flex gap-8">
                            <div className="flex flex-col">
                              <span className="text-[10px] text-[#5f6368] uppercase font-bold tracking-tighter">Actual</span>
                              <span className="text-sm font-medium text-[#202124]">{event.actual}</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] text-[#5f6368] uppercase font-bold tracking-tighter">Forecast</span>
                              <span className="text-sm text-[#5f6368]">{event.forecast || "—"}</span>
                            </div>
                            <div className="flex flex-col">
                              <span className="text-[10px] text-[#5f6368] uppercase font-bold tracking-tighter">Previous</span>
                              <span className="text-sm text-[#5f6368]">{event.previous || "—"}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {activeTab === "indicators" && (
                <section className="bg-white rounded-xl border border-[#dadce0] p-6 shadow-sm">
                  <h3 className="font-medium text-[#202124] mb-6">Historical Indicator View</h3>
                  <div className="h-[400px] w-full bg-[#f8f9fa] rounded-lg border border-dashed border-[#dadce0] flex items-center justify-center">
                    <p className="text-[#5f6368] text-sm">Interactive comparison chart loading...</p>
                  </div>
                </section>
              )}

              {activeTab === "government" && (
                <section className="space-y-4">
                  {governmentData.map((report, i) => (
                    <div key={i} className="bg-white rounded-xl border border-[#dadce0] p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer group">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <FileText className="w-5 h-5 text-[#4285f4]" />
                          <span className="text-xs font-bold text-[#1a73e8] uppercase">{report.source}</span>
                        </div>
                        <span className="text-xs text-[#5f6368]">{new Date(report.date).toLocaleDateString()}</span>
                      </div>
                      <h4 className="text-lg font-medium text-[#202124] mb-2 group-hover:underline">{report.description}</h4>
                      <div className="bg-[#f8f9fa] p-4 rounded-lg border border-[#f1f3f4]">
                        <p className="text-sm text-[#3c4043] leading-relaxed line-clamp-3">{report.value}</p>
                      </div>
                      <div className="mt-4 flex items-center text-[#1a73e8] text-sm font-medium">
                        Read full release <ChevronRight className="w-4 h-4 ml-1" />
                      </div>
                    </div>
                  ))}
                </section>
              )}
            </div>

            <aside className="lg:col-span-4">
              <div className="bg-white rounded-xl border border-[#dadce0] p-6 shadow-sm mb-6">
                <h3 className="font-medium text-[#202124] mb-4 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-[#ea4335]" />
                  Central Bank Rates
                </h3>
                <div className="space-y-4 text-sm font-medium">
                  <div className="flex justify-between items-center py-2 border-b border-[#f1f3f4]">
                    <span className="text-[#5f6368]">Reserve Bank of India (Repo)</span>
                    <span className="text-[#202124]">6.50%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-[#f1f3f4]">
                    <span className="text-[#5f6368]">Federal Reserve (US)</span>
                    <span className="text-[#202124]">5.25% - 5.50%</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-[#5f6368]">European Central Bank</span>
                    <span className="text-[#202124]">4.50%</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#e8f0fe] rounded-2xl p-6 border border-[#d2e3fc]">
                <h3 className="text-lg font-medium text-[#174ea6] mb-2">Economy Intelligence</h3>
                <p className="text-xs text-[#3c4043] leading-relaxed mb-4">Our AI analyzing 1,000+ government gazettes and economic surveys to provide real-time sentiment on the Indian growth trajectory.</p>
                <button className="w-full py-2.5 bg-[#1a73e8] text-white rounded-full text-xs font-bold hover:bg-[#185abc] transition-colors">
                  Request AI Macro Report
                </button>
              </div>

              <div className="mt-8">
                <h3 className="text-xs font-bold text-[#5f6368] uppercase tracking-widest mb-4 px-2">Global resources</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-3 p-3 rounded-xl hover:bg-white border border-transparent hover:border-[#dadce0] transition-all cursor-pointer group">
                    <div className="p-2 bg-blue-50 rounded-lg"><Globe className="w-4 h-4 text-[#1a73e8]" /></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[#202124]">World Bank Open Data</p>
                      <p className="text-[10px] text-[#5f6368]">Global development metrics</p>
                    </div>
                    <ExternalLink className="w-3 h-3 text-[#dadce0] group-hover:text-[#1a73e8]" />
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-xl hover:bg-white border border-transparent hover:border-[#dadce0] transition-all cursor-pointer group">
                    <div className="p-2 bg-purple-50 rounded-lg"><TrendingUp className="w-4 h-4 text-[#720e9e]" /></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[#202124]">IMF Data Mapper</p>
                      <p className="text-[10px] text-[#5f6368]">Economic outlook 2026</p>
                    </div>
                    <ExternalLink className="w-3 h-3 text-[#dadce0] group-hover:text-[#1a73e8]" />
                  </div>
                </div>
              </div>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
