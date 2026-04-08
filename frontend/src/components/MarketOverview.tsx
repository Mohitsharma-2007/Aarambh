import React, { useState, useEffect } from 'react';
import { unifiedAPI } from '@/api/unified';
import { cn } from '@/utils/cn';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Globe, 
  Zap, 
  RefreshCw, 
  Clock,
  BarChart3,
  PieChart,
  Star,
  ArrowUpRight,
  ArrowDownRight,
  Info
} from 'lucide-react';

// Dark theme
const DARK_THEME = {
  colors: {
    primary: "#00D4FF",
    success: "#00FF88",
    danger: "#FF4757",
    warning: "#FFB800",
    bgPrimary: "#0A0B0F",
    bgSecondary: "#0F1419",
    bgCard: "#161B22",
    textPrimary: "#FFFFFF",
    textSecondary: "#8B92A8",
    textMuted: "#5A6278",
    borderDefault: "rgba(255, 255, 255, 0.1)",
  },
  shadows: {
    card: "0 4px 20px rgba(0, 0, 0, 0.5)",
    cardHover: "0 8px 30px rgba(0, 212, 255, 0.2)",
  }
};

interface MarketData {
  section: string;
  title: string;
  count: number;
  items: any[];
  source: string;
}

interface MarketSummary {
  totalStocks: number;
  totalSources: number;
  lastUpdate: string;
}

export default function MarketOverview() {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<MarketSummary>({
    totalStocks: 0,
    totalSources: 0,
    lastUpdate: ''
  });

  const marketSections = [
    { id: 'indexes', label: 'Market Indices', icon: Globe, color: '#00D4FF' },
    { id: 'gainers', label: 'Top Gainers', icon: TrendingUp, color: '#00FF88' },
    { id: 'losers', label: 'Top Losers', icon: TrendingDown, color: '#FF4757' },
    { id: 'most-active', label: 'Most Active', icon: Activity, color: '#FFB800' },
    { id: 'crypto', label: 'Cryptocurrency', icon: Zap, color: '#7C3AED' },
    { id: 'nse-gainers', label: 'NSE Gainers', icon: TrendingUp, color: '#10B981' },
    { id: 'nse-losers', label: 'NSE Losers', icon: TrendingDown, color: '#EF4444' },
    { id: 'nse-active', label: 'NSE Active', icon: Activity, color: '#F59E0B' },
  ];

  const fetchMarketData = async () => {
    setLoading(true);
    const newData: Record<string, MarketData> = {};
    const sources = new Set<string>();
    let totalStocks = 0;

    try {
      // Fetch all market sections in parallel
      const promises = marketSections.map(async (section) => {
        try {
          const result = await unifiedAPI.getGoogleMarket(section.id);
          if (result && result.items) {
            newData[section.id] = result;
            sources.add(result.source);
            totalStocks += result.items.length;
          }
        } catch (error) {
          console.error(`Error fetching ${section.id}:`, error);
        }
      });

      await Promise.all(promises);
      
      setMarketData(newData);
      setSummary({
        totalStocks,
        totalSources: sources.size,
        lastUpdate: new Date().toLocaleTimeString()
      });
    } catch (error) {
      console.error('Error fetching market data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const getDataSourceIcon = (source: string) => {
    switch (source) {
      case 'yahoo_direct':
        return '🌐';
      case 'yahoo_india':
        return '🇮🇳';
      case 'google_finance':
        return '🔍';
      case 'indian_enhanced':
        return '📈';
      case 'fallback':
        return '💾';
      default:
        return '❓';
    }
  };

  const getDataSourceColor = (source: string) => {
    switch (source) {
      case 'yahoo_direct':
        return '#7C3AED';
      case 'yahoo_india':
        return '#10B981';
      case 'google_finance':
        return '#4285F4';
      case 'indian_enhanced':
        return '#F59E0B';
      case 'fallback':
        return '#6B7280';
      default:
        return '#6B7280';
    }
  };

  const formatPrice = (price: string, isIndian: boolean = false) => {
    const currency = isIndian ? '₹' : '$';
    return `${currency}${price}`;
  };

  const isPositive = (change: string) => {
    return !change?.includes("-") && !change?.includes("0.00");
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
              Market Overview
            </h1>
            <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Real-time market data from multiple sources
            </p>
          </div>
          <button
            onClick={fetchMarketData}
            disabled={loading}
            className="px-4 py-2 rounded-xl font-medium text-sm transition-all flex items-center gap-2"
            style={{
              backgroundColor: DARK_THEME.colors.primary,
              color: DARK_THEME.colors.textPrimary,
              boxShadow: DARK_THEME.shadows.card,
            }}
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div
            className="p-6 rounded-2xl border"
            style={{
              backgroundColor: DARK_THEME.colors.bgCard,
              borderColor: DARK_THEME.colors.borderDefault,
              boxShadow: DARK_THEME.shadows.card,
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <BarChart3 className="w-8 h-8" style={{ color: DARK_THEME.colors.primary }} />
              <span className="text-2xl font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
                {summary.totalStocks}
              </span>
            </div>
            <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Total Stocks Tracked
            </p>
          </div>

          <div
            className="p-6 rounded-2xl border"
            style={{
              backgroundColor: DARK_THEME.colors.bgCard,
              borderColor: DARK_THEME.colors.borderDefault,
              boxShadow: DARK_THEME.shadows.card,
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <PieChart className="w-8 h-8" style={{ color: DARK_THEME.colors.success }} />
              <span className="text-2xl font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
                {summary.totalSources}
              </span>
            </div>
            <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Active Data Sources
            </p>
          </div>

          <div
            className="p-6 rounded-2xl border"
            style={{
              backgroundColor: DARK_THEME.colors.bgCard,
              borderColor: DARK_THEME.colors.borderDefault,
              boxShadow: DARK_THEME.shadows.card,
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8" style={{ color: DARK_THEME.colors.warning }} />
              <span className="text-lg font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
                {summary.lastUpdate}
              </span>
            </div>
            <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Last Updated
            </p>
          </div>
        </div>

        {/* Market Sections Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* US Markets */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
              <Globe className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
              US Markets
            </h2>
            <div className="space-y-4">
              {marketSections.slice(0, 4).map((section) => {
                const data = marketData[section.id];
                return (
                  <div
                    key={section.id}
                    className="p-4 rounded-2xl border transition-all"
                    style={{
                      backgroundColor: DARK_THEME.colors.bgCard,
                      borderColor: DARK_THEME.colors.borderDefault,
                      boxShadow: DARK_THEME.shadows.card,
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <section.icon className="w-4 h-4" style={{ color: section.color }} />
                        <h3 className="font-semibold" style={{ color: DARK_THEME.colors.textPrimary }}>
                          {section.label}
                        </h3>
                      </div>
                      {data && (
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>
                            {data.count} items
                          </span>
                          <div className="flex items-center gap-1 px-2 py-1 rounded"
                            style={{
                              backgroundColor: `${getDataSourceColor(data.source)}20`,
                              color: getDataSourceColor(data.source),
                            }}
                          >
                            <span className="text-xs">{getDataSourceIcon(data.source)}</span>
                            <span className="text-xs">{data.source}</span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {data && data.items.length > 0 && (
                      <div className="space-y-2">
                        {data.items.slice(0, 3).map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-2 rounded-lg"
                            style={{
                              backgroundColor: DARK_THEME.colors.bgSecondary,
                            }}
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm" style={{ 
                                  fontFamily: 'monospace',
                                  color: DARK_THEME.colors.textPrimary 
                                }}>
                                  {item.ticker || item.symbol}
                                </span>
                                <span className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                                  {item.name}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-sm" style={{ 
                                fontFamily: 'monospace',
                                color: DARK_THEME.colors.textPrimary 
                              }}>
                                {formatPrice(item.price || item.value || '0.00')}
                              </p>
                              <div className="flex items-center gap-1">
                                {isPositive(item.change || item.change_percent) ? (
                                  <ArrowUpRight className="w-3 h-3" style={{ color: DARK_THEME.colors.success }} />
                                ) : (
                                  <ArrowDownRight className="w-3 h-3" style={{ color: DARK_THEME.colors.danger }} />
                                )}
                                <span className="text-xs" style={{ 
                                  color: isPositive(item.change || item.change_percent) 
                                    ? DARK_THEME.colors.success 
                                    : DARK_THEME.colors.danger 
                                }}>
                                  {item.change || item.change_percent || '0.00%'}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Indian Markets */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
              <span className="text-lg">🇮🇳</span>
              Indian Markets
            </h2>
            <div className="space-y-4">
              {marketSections.slice(5).map((section) => {
                const data = marketData[section.id];
                return (
                  <div
                    key={section.id}
                    className="p-4 rounded-2xl border transition-all"
                    style={{
                      backgroundColor: DARK_THEME.colors.bgCard,
                      borderColor: DARK_THEME.colors.borderDefault,
                      boxShadow: DARK_THEME.shadows.card,
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <section.icon className="w-4 h-4" style={{ color: section.color }} />
                        <h3 className="font-semibold" style={{ color: DARK_THEME.colors.textPrimary }}>
                          {section.label}
                        </h3>
                      </div>
                      {data && (
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>
                            {data.count} items
                          </span>
                          <div className="flex items-center gap-1 px-2 py-1 rounded"
                            style={{
                              backgroundColor: `${getDataSourceColor(data.source)}20`,
                              color: getDataSourceColor(data.source),
                            }}
                          >
                            <span className="text-xs">{getDataSourceIcon(data.source)}</span>
                            <span className="text-xs">{data.source}</span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {data && data.items.length > 0 && (
                      <div className="space-y-2">
                        {data.items.slice(0, 3).map((item, index) => (
                          <div key={index} className="flex items-center justify-between p-2 rounded-lg"
                            style={{
                              backgroundColor: DARK_THEME.colors.bgSecondary,
                            }}
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm" style={{ 
                                  fontFamily: 'monospace',
                                  color: DARK_THEME.colors.textPrimary 
                                }}>
                                  {item.ticker || item.symbol}
                                </span>
                                <span className="text-xs px-2 py-1 rounded" style={{
                                  backgroundColor: DARK_THEME.colors.warning + '20',
                                  color: DARK_THEME.colors.warning,
                                }}>
                                  NSE
                                </span>
                                <span className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                                  {item.name}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-sm" style={{ 
                                fontFamily: 'monospace',
                                color: DARK_THEME.colors.textPrimary 
                              }}>
                                {formatPrice(item.price || item.value || '0.00', true)}
                              </p>
                              <div className="flex items-center gap-1">
                                {isPositive(item.change || item.change_percent) ? (
                                  <ArrowUpRight className="w-3 h-3" style={{ color: DARK_THEME.colors.success }} />
                                ) : (
                                  <ArrowDownRight className="w-3 h-3" style={{ color: DARK_THEME.colors.danger }} />
                                )}
                                <span className="text-xs" style={{ 
                                  color: isPositive(item.change || item.change_percent) 
                                    ? DARK_THEME.colors.success 
                                    : DARK_THEME.colors.danger 
                                }}>
                                  {item.change || item.change_percent || '0.00%'}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
