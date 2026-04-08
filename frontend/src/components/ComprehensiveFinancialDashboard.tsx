import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Responsive, AreaChart, Area, ComposedChart } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign, Building2, Users, Globe, BarChart3, PieChart, FileText, Calendar, Target, AlertTriangle, Newspaper, Brain, MessageCircle, Share2, Eye, ThumbsUp, ThumbsDown, Star, Zap, TrendingUpIcon, TrendingDownIcon } from 'lucide-react';

// Dark theme
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

interface AIAnalysis {
  overall_health: string;
  recommendation: string;
  confidence: number;
  strengths: string[];
  weaknesses: string[];
  market_outlook: any;
  risk_analysis: any;
  target_price: any;
  social_media_sentiment: any;
  competitive_position: any;
}

interface SocialInsights {
  platforms: any;
  overall_metrics: any;
  analysis: any;
  ai_models: any;
}

// Components
const DarkCard = ({ children, className = "", accent }: { children: React.ReactNode; className?: string; accent?: string }) => (
  <div 
    className={`rounded-2xl border-2 transition-all hover:shadow-lg ${className}`}
    style={{
      backgroundColor: DARK_THEME.colors.bgCard,
      borderColor: accent || DARK_THEME.colors.borderDefault,
      boxShadow: DARK_THEME.shadows.card,
    }}
  >
    {children}
  </div>
);

const MarketIndicesCard = ({ indices }: { indices: MarketIndex[] }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <Globe className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      Market Indices
    </h3>
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
      {indices.map((index, i) => (
        <div key={i} className="p-3 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>
              {index.name}
            </span>
            <span className="text-xs px-2 py-1 rounded" style={{ 
              backgroundColor: index.change_percent.includes('+') ? DARK_THEME.colors.success + "20" : DARK_THEME.colors.danger + "20",
              color: index.change_percent.includes('+') ? DARK_THEME.colors.success : DARK_THEME.colors.danger
            }}>
              {index.change_percent}
            </span>
          </div>
          <div className="text-lg font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {index.price}
          </div>
          <div className="text-sm" style={{ color: DARK_THEME.colors.textMuted, fontFamily: 'monospace' }}>
            {index.change}
          </div>
        </div>
      ))}
    </div>
  </DarkCard>
);

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
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
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
              <Bar dataKey="high" fill={DARK_THEME.colors.success} />
              <Bar dataKey="low" fill={DARK_THEME.colors.danger} />
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
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
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
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
              />
              <YAxis 
                stroke={DARK_THEME.colors.textMuted}
                tick={{ fill: DARK_THEME.colors.textMuted, fontSize: 12 }}
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
    <DarkCard className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          <BarChart3 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
          {symbol} Charts
        </h3>
        <div className="flex gap-2">
          {['candlestick', 'bar', 'line'].map((type) => (
            <button
              key={type}
              onClick={() => onChartTypeChange(type)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
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
      <div className="h-96">
        {renderChart()}
      </div>
    </DarkCard>
  );
};

const CompanyDetailsCard = ({ companyData }: { companyData: CompanyData }) => {
  const profile = companyData.company_profile || {};
  const quote = companyData.quote || {};
  
  return (
    <DarkCard className="p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
        <Building2 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
        Company Details
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Company Name</label>
            <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary }}>
              {profile.name || companyData.symbol}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Sector</label>
            <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>
              {profile.sector || 'N/A'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Industry</label>
            <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>
              {profile.industry || 'N/A'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Exchange</label>
            <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>
              {profile.exchange || 'N/A'}
            </p>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Current Price</label>
            <p className="text-2xl font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
              ${quote.price || '0.00'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Market Cap</label>
            <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
              ${(profile.market_cap / 1000000000).toFixed(2)}B
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>P/E Ratio</label>
            <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
              {profile.pe_ratio?.toFixed(2) || 'N/A'}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Employees</label>
            <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary }}>
              {profile.employees?.toLocaleString() || 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </DarkCard>
  );
};

const NewsCard = ({ news }: { news: NewsItem[] }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <Newspaper className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      Latest News
    </h3>
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {news.map((article, i) => (
        <div key={i} className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="flex items-start gap-3">
            {article.image && (
              <img 
                src={article.image} 
                alt={article.headline}
                className="w-16 h-16 rounded-lg object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
            <div className="flex-1">
              <h4 className="font-semibold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
                {article.headline}
              </h4>
              <p className="text-sm mb-2" style={{ color: DARK_THEME.colors.textSecondary }}>
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
                    className="text-blue-400 hover:text-blue-300 text-sm"
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

const AIAnalysisCard = ({ aiAnalysis, socialInsights }: { aiAnalysis: AIAnalysis; socialInsights: SocialInsights }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <Brain className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      FINAI Analysis
    </h3>
    
    <div className="space-y-6">
      {/* AI Models Status */}
      <div className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="font-semibold mb-3 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          <Zap className="w-4 h-4" style={{ color: DARK_THEME.colors.warning }} />
          AI Models Status
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Google Gemini: Active
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Groww AI: Active
            </span>
          </div>
        </div>
      </div>

      {/* Investment Recommendation */}
      <div className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="font-semibold mb-3" style={{ color: DARK_THEME.colors.textPrimary }}>
          Investment Recommendation
        </h4>
        <div className="flex items-center justify-between">
          <div>
            <div className={`text-2xl font-bold px-4 py-2 rounded-lg ${
              aiAnalysis.recommendation === 'Buy' ? 'bg-green-500 text-white' :
              aiAnalysis.recommendation === 'Sell' ? 'bg-red-500 text-white' :
              'bg-yellow-500 text-black'
            }`}>
              {aiAnalysis.recommendation}
            </div>
            <div className="text-sm mt-2" style={{ color: DARK_THEME.colors.textMuted }}>
              Confidence: {aiAnalysis.confidence}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Target Price
            </div>
            <div className="text-xl font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
              {aiAnalysis.target_price?.target || 'N/A'}
            </div>
            <div className="text-sm" style={{ color: DARK_THEME.colors.textMuted, fontFamily: 'monospace' }}>
              Range: {aiAnalysis.target_price?.range?.low || 'N/A'} - {aiAnalysis.target_price?.range?.high || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Social Media Insights */}
      <div className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
        <h4 className="font-semibold mb-3 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
          <MessageCircle className="w-4 h-4" style={{ color: DARK_THEME.colors.info }} />
          Social Media Insights
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm mb-2" style={{ color: DARK_THEME.colors.textSecondary }}>
              Overall Sentiment
            </div>
            <div className="flex items-center gap-2">
              <div className={`text-lg font-bold ${
                socialInsights.overall_metrics?.overall_sentiment === 'Positive' ? 'text-green-400' :
                socialInsights.overall_metrics?.overall_sentiment === 'Negative' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {socialInsights.overall_metrics?.overall_sentiment || 'Neutral'}
              </div>
              <div className="text-sm" style={{ color: DARK_THEME.colors.textMuted }}>
                ({(socialInsights.overall_metrics?.sentiment_score || 0.5 * 100).toFixed(0)}%)
              </div>
            </div>
          </div>
          <div>
            <div className="text-sm mb-2" style={{ color: DARK_THEME.colors.textSecondary }}>
              Trend Direction
            </div>
            <div className="flex items-center gap-2">
              {socialInsights.overall_metrics?.trend_direction === 'Improving' ? (
                <TrendingUpIcon className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingDownIcon className="w-5 h-5 text-red-400" />
              )}
              <span className="text-lg font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
                {socialInsights.overall_metrics?.trend_direction || 'Stable'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t" style={{ borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="text-sm font-medium mb-2" style={{ color: DARK_THEME.colors.textSecondary }}>
            Key Mentions
          </div>
          <div className="flex flex-wrap gap-2">
            {(socialInsights.overall_metrics?.key_mentions || []).map((mention: string, i: number) => (
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

      {/* Strengths and Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <h4 className="font-semibold mb-3 flex items-center gap-2" style={{ color: DARK_THEME.colors.success }}>
            <ThumbsUp className="w-4 h-4" />
            Strengths
          </h4>
          <ul className="space-y-2">
            {(aiAnalysis.strengths || []).map((strength: string, i: number) => (
              <li key={i} className="text-sm flex items-start gap-2" style={{ color: DARK_THEME.colors.textSecondary }}>
                <Star className="w-3 h-3 text-green-400 mt-0.5" />
                {strength}
              </li>
            ))}
          </ul>
        </div>
        <div className="p-4 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <h4 className="font-semibold mb-3 flex items-center gap-2" style={{ color: DARK_THEME.colors.danger }}>
            <ThumbsDown className="w-4 h-4" />
            Weaknesses
          </h4>
          <ul className="space-y-2">
            {(aiAnalysis.weaknesses || []).map((weakness: string, i: number) => (
              <li key={i} className="text-sm flex items-start gap-2" style={{ color: DARK_THEME.colors.textSecondary }}>
                <AlertTriangle className="w-3 h-3 text-red-400 mt-0.5" />
                {weakness}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  </DarkCard>
);

// Main Component
export default function ComprehensiveFinancialDashboard({ symbol }: { symbol: string }) {
  const [marketIndices, setMarketIndices] = useState<MarketIndex[]>([]);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [chartType, setChartType] = useState<'candlestick' | 'bar' | 'line'>('candlestick');
  const [companyData, setCompanyData] = useState<CompanyData | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [socialInsights, setSocialInsights] = useState<SocialInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all data in parallel
        const [
          indicesResponse,
          chartResponse,
          companyResponse,
          newsResponse,
          aiResponse,
          socialResponse
        ] = await Promise.all([
          fetch('/api/dashboard/market/indices').then(r => r.json()),
          fetch(`/api/dashboard/charts/${symbol}/${chartType}`).then(r => r.json()),
          fetch(`/api/dashboard/company/${symbol}/complete`).then(r => r.json()),
          fetch(`/api/dashboard/company/${symbol}/news`).then(r => r.json()),
          fetch(`/api/dashboard/company/${symbol}/ai-analysis`).then(r => r.json()),
          fetch(`/api/dashboard/company/${symbol}/social-insights`).then(r => r.json()),
        ]);

        // Process responses
        if (indicesResponse.dashboard?.market_indices?.indices) {
          setMarketIndices(indicesResponse.dashboard.market_indices.indices);
        }

        if (chartResponse.chart_data?.data) {
          const processedData = chartResponse.chart_data.data.candlestick || chartResponse.chart_data.data.line || chartResponse.chart_data.data.bar || [];
          setChartData(processedData);
        }

        if (companyResponse.company_details) {
          setCompanyData(companyResponse.company_details);
        }

        if (newsResponse.news?.news) {
          setNews(newsResponse.news.news);
        }

        if (aiResponse.ai_analysis) {
          setAiAnalysis(aiResponse.ai_analysis.ai_analysis);
        }

        if (socialResponse.social_insights) {
          setSocialInsights(socialResponse.social_insights);
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
          <p style={{ color: DARK_THEME.colors.textSecondary }}>Loading comprehensive financial dashboard...</p>
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
    <div className="min-h-screen p-6" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
            Comprehensive Financial Dashboard
          </h1>
          <p className="text-lg" style={{ color: DARK_THEME.colors.textSecondary }}>
            {symbol} - Real-time Analysis & Insights
          </p>
        </div>

        {/* Section 1: Market Indices */}
        <MarketIndicesCard indices={marketIndices} />

        {/* Section 2: Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

        {/* Section 3: News and AI Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <NewsCard news={news} />
          <AIAnalysisCard 
            aiAnalysis={aiAnalysis || { 
              overall_health: 'Positive',
              recommendation: 'Hold',
              confidence: 75,
              strengths: [],
              weaknesses: [],
              market_outlook: {},
              risk_analysis: {},
              target_price: {},
              social_media_sentiment: {},
              competitive_position: {}
            }}
            socialInsights={socialInsights || {
              platforms: {},
              overall_metrics: {},
              analysis: {},
              ai_models: {}
            }}
          />
        </div>
      </div>
    </div>
  );
}
