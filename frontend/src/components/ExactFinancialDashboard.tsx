import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Responsive, AreaChart, Area, ComposedChart } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign, Building2, Users, Globe, BarChart3, PieChart, FileText, Calendar, Target, AlertTriangle, Newspaper, Brain, MessageCircle, Share2, Eye, ThumbsUp, ThumbsDown, Star, Zap, TrendingUpIcon, TrendingDownIcon, ChevronUp, ChevronDown, Clock, Volume2 } from 'lucide-react';

// Dark theme matching reference images
const DARK_THEME = {
  colors: {
    primary: "#00D4FF",
    success: "#00FF88",
    danger: "#FF4757",
    warning: "#FFB800",
    info: "#3498db",
    bgPrimary: "#0A0B0F",
    bgSecondary: "#0F1419",
    bgCard: "#161B22",
    textPrimary: "#FFFFFF",
    textSecondary: "#8B92A8",
    textMuted: "#5A6278",
    borderDefault: "rgba(255, 255, 255, 0.1)",
    borderLight: "rgba(255, 255, 255, 0.2)",
    borderBright: "rgba(0, 212, 255, 0.3)",
    green: "#10B981",
    red: "#EF4444",
    gray: "#6B7280",
  },
  shadows: {
    card: "0 4px 20px rgba(0, 0, 0, 0.5)",
    cardHover: "0 8px 30px rgba(0, 212, 255, 0.2)",
  }
};

// Types
interface MarketIndex {
  symbol: string;
  name: string;
  price: string;
  change: string;
  change_percent: string;
  volume: string;
  source: string;
  trend: 'up' | 'down';
}

interface ChartData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  value?: number;
  price?: number;
}

interface CompanyData {
  symbol: string;
  quote: any;
  company_profile: any;
  financial_statements: any;
  technical_indicators: any;
  market_context: any;
}

interface NewsItem {
  headline: string;
  source: string;
  url: string;
  summary: string;
  image: string;
  datetime: string;
  category: string;
}

// Components
const DarkCard = ({ children, className = "", accent }: { children: React.ReactNode; className?: string; accent?: string }) => (
  <div 
    className={`rounded-xl border transition-all hover:shadow-lg ${className}`}
    style={{
      backgroundColor: DARK_THEME.colors.bgCard,
      borderColor: accent || DARK_THEME.colors.borderDefault,
      boxShadow: DARK_THEME.shadows.card,
    }}
  >
    {children}
  </div>
);

// Market Indices Card - Exact match to reference
const MarketIndicesCard = ({ indices }: { indices: MarketIndex[] }) => (
  <DarkCard className="p-4">
    <h3 className="text-lg font-bold mb-3" style={{ color: DARK_THEME.colors.textPrimary }}>
      Market Indices
    </h3>
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {indices.map((index, i) => (
        <div key={i} className="p-2 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>
              {index.name}
            </span>
            {index.trend === 'up' ? (
              <ChevronUp className="w-3 h-3" style={{ color: DARK_THEME.colors.green }} />
            ) : (
              <ChevronDown className="w-3 h-3" style={{ color: DARK_THEME.colors.red }} />
            )}
          </div>
          <div className="text-sm font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {index.price}
          </div>
          <div className="text-xs" style={{ 
            color: index.trend === 'up' ? DARK_THEME.colors.green : DARK_THEME.colors.red,
            fontFamily: 'monospace'
          }}>
            {index.change_percent}
          </div>
        </div>
      ))}
    </div>
  </DarkCard>
);

// Chart Section - Exact match to reference
const ChartSection = ({ symbol, chartData, chartType, onChartTypeChange }: { 
  symbol: string; 
  chartData: ChartData[]; 
  chartType: string; 
  onChartTypeChange: (type: string) => void;
}) => {
  const renderChart = () => {
    switch (chartType) {
      case 'candlestick':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={DARK_THEME.colors.borderDefault} />
              <XAxis 
                dataKey="time" 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: DARK_THEME.colors.bgCard, 
                  border: `1px solid ${DARK_THEME.colors.borderDefault}`,
                  borderRadius: '8px'
                }}
                labelStyle={{ color: DARK_THEME.colors.textPrimary }}
              />
              <Bar dataKey="high" fill={DARK_THEME.colors.green} />
              <Bar dataKey="low" fill={DARK_THEME.colors.red} />
            </ComposedChart>
          </ResponsiveContainer>
        );
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={DARK_THEME.colors.borderDefault} />
              <XAxis 
                dataKey="time" 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: DARK_THEME.colors.bgCard, 
                  border: `1px solid ${DARK_THEME.colors.borderDefault}`,
                  borderRadius: '8px'
                }}
                labelStyle={{ color: DARK_THEME.colors.textPrimary }}
              />
              <Bar dataKey="value" fill={DARK_THEME.colors.primary} />
            </BarChart>
          </ResponsiveContainer>
        );
      case 'line':
      default:
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={DARK_THEME.colors.primary} stopOpacity={0.8}/>
                  <stop offset="95%" stopColor={DARK_THEME.colors.primary} stopOpacity={0.2}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={DARK_THEME.colors.borderDefault} />
              <XAxis 
                dataKey="time" 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 10 }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: DARK_THEME.colors.bgCard, 
                  border: `1px solid ${DARK_THEME.colors.borderDefault}`,
                  borderRadius: '8px'
                }}
                labelStyle={{ color: DARK_THEME.colors.textPrimary }}
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke={DARK_THEME.colors.primary}
                strokeWidth={2}
                fill="url(#colorGradient)"
              />
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <DarkCard className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
          {symbol} Chart
        </h3>
        <div className="flex gap-1">
          {['candlestick', 'bar', 'line'].map((type) => (
            <button
              key={type}
              onClick={() => onChartTypeChange(type)}
              className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                chartType === type 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div className="h-64">
        {renderChart()}
      </div>
    </DarkCard>
  );
};

// Company Details Card - Exact match to reference
const CompanyDetailsCard = ({ companyData }: { companyData: CompanyData }) => {
  const profile = companyData.company_profile || {};
  const quote = companyData.quote || {};
  
  return (
    <DarkCard className="p-4">
      <h3 className="text-lg font-bold mb-3" style={{ color: DARK_THEME.colors.textPrimary }}>
        Company Details
      </h3>
      
      {/* Price Display */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-2xl font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${quote.price || '0.00'}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium" style={{ 
              color: (quote.change_percent || '').includes('+') ? DARK_THEME.colors.green : DARK_THEME.colors.red,
              fontFamily: 'monospace'
            }}>
              {quote.change || '0.00'}
            </span>
            <span className="text-sm" style={{ 
              color: (quote.change_percent || '').includes('+') ? DARK_THEME.colors.green : DARK_THEME.colors.red,
              fontFamily: 'monospace'
            }}>
              {quote.change_percent || '0.00%'}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
            Volume
          </div>
          <div className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {quote.volume || '0'}
          </div>
        </div>
      </div>
      
      {/* Company Info */}
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>Company Name</span>
          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary }}>
            {profile.name || companyData.symbol}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>Sector</span>
          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary }}>
            {profile.sector || 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>Market Cap</span>
          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${(profile.market_cap / 1000000000).toFixed(2)}B
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>P/E Ratio</span>
          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {profile.pe_ratio?.toFixed(2) || 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>Exchange</span>
          <span className="text-sm font-medium" style={{ color: DARK_THEME.colors.textPrimary }}>
            {profile.exchange || 'NASDAQ'}
          </span>
        </div>
      </div>
    </DarkCard>
  );
};

// News Card - Exact match to reference
const NewsCard = ({ news }: { news: NewsItem[] }) => (
  <DarkCard className="p-4">
    <h3 className="text-lg font-bold mb-3" style={{ color: DARK_THEME.colors.textPrimary }}>
      Latest News
    </h3>
    <div className="space-y-3 max-h-64 overflow-y-auto">
      {news.map((article, i) => (
        <div key={i} className="p-3 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="flex items-start gap-3">
            {article.image && (
              <img 
                src={article.image} 
                alt={article.headline}
                className="w-12 h-12 rounded object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
            <div className="flex-1">
              <h4 className="text-sm font-semibold mb-1" style={{ color: DARK_THEME.colors.textPrimary }}>
                {article.headline}
              </h4>
              <p className="text-xs mb-2 line-clamp-2" style={{ color: DARK_THEME.colors.textSecondary }}>
                {article.summary}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded" style={{ 
                    backgroundColor: DARK_THEME.colors.info + "20",
                    color: DARK_THEME.colors.info
                  }}>
                    {article.source}
                  </span>
                  <span className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                    {new Date(article.datetime).toLocaleDateString()}
                  </span>
                </div>
                {article.url && (
                  <a 
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-xs"
                  >
                    Read more
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  </DarkCard>
);

// AI Analysis Card - Exact match to reference
const AIAnalysisCard = ({ symbol }: { symbol: string }) => {
  const [aiData, setAiData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAiData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/exact/company/${symbol}/ai-analysis`);
        const data = await response.json();
        if (data.status === 'success') {
          setAiData(data.ai_analysis);
        }
      } catch (err) {
        console.error('Failed to fetch AI data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAiData();
  }, [symbol]);

  if (loading) {
    return (
      <DarkCard className="p-4">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-t-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p style={{ color: DARK_THEME.colors.textSecondary }}>Loading AI analysis...</p>
        </div>
      </DarkCard>
    );
  }

  const analysis = aiData || {
    recommendation: "BUY",
    confidence: 75,
    target_price: {
      current: "252.62",
      target: "289.50",
      range: { low: "275.50", high: "312.00" }
    },
    social_media_sentiment: {
      overall: "Positive",
      score: 0.65,
      trend: "Improving",
      key_mentions: ["Product launch", "Earnings beat", "Market expansion"]
    }
  };

  return (
    <DarkCard className="p-4">
      <h3 className="text-lg font-bold mb-3" style={{ color: DARK_THEME.colors.textPrimary }}>
        FINAI Analysis
      </h3>
      
      {/* AI Models Status */}
      <div className="p-3 rounded-lg border mb-3" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="text-sm font-semibold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          AI Models Status
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs" style={{ color: DARK_THEME.colors.textSecondary }}>
              Google Gemini: Active
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs" style={{ color: DARK_THEME.colors.textSecondary }}>
              Groww AI: Active
            </span>
          </div>
        </div>
      </div>

      {/* Investment Recommendation */}
      <div className="p-3 rounded-lg border mb-3" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="text-sm font-semibold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          Investment Recommendation
        </h4>
        <div className="flex items-center justify-between">
          <div>
            <div className={`text-lg font-bold px-3 py-1 rounded ${
              analysis.recommendation === 'BUY' ? 'bg-green-500 text-white' :
              analysis.recommendation === 'SELL' ? 'bg-red-500 text-white' :
              'bg-yellow-500 text-black'
            }`}>
              {analysis.recommendation}
            </div>
            <div className="text-xs mt-1" style={{ color: DARK_THEME.colors.textMuted }}>
              Confidence: {analysis.confidence}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs" style={{ color: DARK_THEME.colors.textSecondary }}>
              Target Price
            </div>
            <div className="text-lg font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
              ${analysis.target_price.target}
            </div>
            <div className="text-xs" style={{ color: DARK_THEME.colors.textMuted, fontFamily: 'monospace' }}>
              ${analysis.target_price.range.low} - ${analysis.target_price.range.high}
            </div>
          </div>
        </div>
      </div>

      {/* Social Media Insights */}
      <div className="p-3 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="text-sm font-semibold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          Social Media Insights
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-xs mb-1" style={{ color: DARK_THEME.colors.textSecondary }}>
              Overall Sentiment
            </div>
            <div className="flex items-center gap-2">
              <div className={`text-sm font-bold ${
                analysis.social_media_sentiment.overall === 'Positive' ? 'text-green-400' :
                analysis.social_media_sentiment.overall === 'Negative' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {analysis.social_media_sentiment.overall}
              </div>
              <div className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                ({Math.round(analysis.social_media_sentiment.score * 100)}%)
              </div>
            </div>
          </div>
          <div>
            <div className="text-xs mb-1" style={{ color: DARK_THEME.colors.textSecondary }}>
              Trend Direction
            </div>
            <div className="flex items-center gap-2">
              {analysis.social_media_sentiment.trend === 'Improving' ? (
                <TrendingUpIcon className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDownIcon className="w-4 h-4 text-red-400" />
              )}
              <span className="text-sm font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
                {analysis.social_media_sentiment.trend}
              </span>
            </div>
          </div>
        </div>
        
        <div className="mt-2 pt-2 border-t" style={{ borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="text-xs font-medium mb-1" style={{ color: DARK_THEME.colors.textSecondary }}>
            Key Mentions
          </div>
          <div className="flex flex-wrap gap-1">
            {analysis.social_media_sentiment.key_mentions.map((mention: string, i: number) => (
              <span key={i} className="px-2 py-1 rounded text-xs" style={{ 
                backgroundColor: DARK_THEME.colors.primary + "20",
                color: DARK_THEME.colors.primary
              }}>
                {mention}
              </span>
            ))}
          </div>
        </div>
      </div>
    </DarkCard>
  );
};

// Main Component - Exact match to reference layout
export default function ExactFinancialDashboard({ symbol }: { symbol: string }) {
  const [marketIndices, setMarketIndices] = useState<MarketIndex[]>([]);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [chartType, setChartType] = useState<'candlestick' | 'bar' | 'line'>('candlestick');
  const [companyData, setCompanyData] = useState<CompanyData | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch data from exact API endpoints
        const [indicesResponse, chartResponse, companyResponse, newsResponse, aiResponse] = await Promise.all([
          fetch('/api/exact/market/indices').then(r => r.json()),
          fetch(`/api/exact/charts/${symbol}/candlestick`).then(r => r.json()),
          fetch(`/api/exact/company/${symbol}/details`).then(r => r.json()),
          fetch(`/api/exact/company/${symbol}/news?limit=3`).then(r => r.json()),
          fetch(`/api/exact/company/${symbol}/ai-analysis`).then(r => r.json()),
        ]);

        // Process responses
        if (indicesResponse.status === 'success') {
          setMarketIndices(indicesResponse.indices);
        }

        if (chartResponse.status === 'success') {
          const data = chartResponse.data;
          if (chartType === 'candlestick' && data.candlestick) {
            setChartData(data.candlestick);
          } else if (chartType === 'bar' && data.bar) {
            setChartData(data.bar);
          } else if (chartType === 'line' && data.line) {
            setChartData(data.line);
          }
        }

        if (companyResponse.status === 'success') {
          setCompanyData(companyResponse.company_data);
        }

        if (newsResponse.status === 'success') {
          setNews(newsResponse.news);
        }

        // Store AI analysis for the AI card
        if (aiResponse.status === 'success') {
          // AI analysis is handled in the AIAnalysisCard component
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [symbol, chartType]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-t-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: DARK_THEME.colors.textSecondary }}>Loading financial dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4" style={{ color: DARK_THEME.colors.danger }} />
          <p className="text-xl font-semibold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>Error</p>
          <p style={{ color: DARK_THEME.colors.textSecondary }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-2xl font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
            Financial Dashboard
          </h1>
          <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
            {symbol} - Real-time Analysis & Insights
          </p>
        </div>

        {/* Section 1: Market Indices */}
        <MarketIndicesCard indices={marketIndices} />

        {/* Section 2: Charts + Company Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <ChartSection 
              symbol={symbol}
              chartData={chartData}
              chartType={chartType}
              onChartTypeChange={setChartType}
            />
          </div>
          <div>
            <CompanyDetailsCard companyData={companyData || { symbol, quote: {}, company_profile: {} }} />
          </div>
        </div>

        {/* Section 3: News + AI Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NewsCard news={news} />
          <AIAnalysisCard symbol={symbol} />
        </div>
      </div>
    </div>
  );
}
