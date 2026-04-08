import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Activity, DollarSign, Building2, Users, Globe, BarChart3, PieChart, FileText, Calendar, Target, AlertTriangle } from 'lucide-react';

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
interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'buy' | 'sell' | 'neutral';
  color: string;
}

interface CompanyProfile {
  symbol: string;
  name: string;
  description: string;
  sector: string;
  industry: string;
  market_cap: number;
  pe_ratio: number;
  pb_ratio: number;
  dividend_yield: number;
  eps: number;
  revenue: number;
  net_income: number;
  employees: number;
  website: string;
  ceo: string;
  exchange: string;
  country: string;
  beta: number;
  target_price: number;
  high_52w: number;
  low_52w: number;
}

interface FinancialStatement {
  revenue: number;
  net_income: number;
  total_assets: number;
  total_liabilities: number;
  operating_cash_flow: number;
  free_cash_flow: number;
  gross_margin: number;
  operating_margin: number;
  net_margin: number;
  roe: number;
  roa: number;
  debt_to_equity: number;
  current_ratio: number;
  quick_ratio: number;
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

const StockPrice = ({ price, change, changePercent, currency = "$" }: {
  price: string;
  change: string;
  changePercent: string;
  currency?: string
}) => {
  const isPositive = !change?.includes("-") && !changePercent?.includes("-");
  const color = isPositive ? DARK_THEME.colors.success : DARK_THEME.colors.danger;

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <div className="text-3xl font-bold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
          {currency}{price}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-lg font-medium" style={{ color, fontFamily: 'monospace' }}>
            {isPositive ? '+' : ''}{change}
          </span>
          <span className="text-lg font-medium" style={{ color, fontFamily: 'monospace' }}>
            ({isPositive ? '+' : ''}{changePercent})
          </span>
        </div>
      </div>
    </div>
  );
};

const TechnicalIndicatorsPanel = ({ indicators }: { indicators: TechnicalIndicator[] }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <BarChart3 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      Technical Indicators
    </h3>
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {indicators.map((indicator, index) => (
        <div key={index} className="p-3 rounded-lg border" style={{ backgroundColor: DARK_THEME.colors.bgSecondary, borderColor: DARK_THEME.colors.borderDefault }}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>
              {indicator.name}
            </span>
            <div className={`px-2 py-1 rounded text-xs font-medium ${indicator.signal === 'buy' ? 'bg-green-500/20 text-green-400' :
              indicator.signal === 'sell' ? 'bg-red-500/20 text-red-400' :
                'bg-yellow-500/20 text-yellow-400'
              }`}>
              {indicator.signal.toUpperCase()}
            </div>
          </div>
          <div className="text-2xl font-bold" style={{ color: indicator.color, fontFamily: 'monospace' }}>
            {indicator.value.toFixed(2)}
          </div>
        </div>
      ))}
    </div>
  </DarkCard>
);

const CompanyProfileCard = ({ profile }: { profile: CompanyProfile }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <Building2 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      Company Profile
    </h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Company Name</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary }}>{profile.name}</p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Sector</label>
          <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>{profile.sector}</p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Industry</label>
          <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>{profile.industry}</p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Exchange</label>
          <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>{profile.exchange}</p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Country</label>
          <p className="text-lg" style={{ color: DARK_THEME.colors.textPrimary }}>{profile.country}</p>
        </div>
      </div>
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Market Cap</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${(profile.market_cap / 1000000000).toFixed(2)}B
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>P/E Ratio</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {profile.pe_ratio.toFixed(2)}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>P/B Ratio</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {profile.pb_ratio.toFixed(2)}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Dividend Yield</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {(profile.dividend_yield * 100).toFixed(2)}%
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>EPS</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${profile.eps.toFixed(2)}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Beta</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {typeof profile.beta === 'number' ? profile.beta.toFixed(2) : (profile.beta || '—')}
          </p>
        </div>
      </div>
    </div>
  </DarkCard>
);

const FinancialStatementsCard = ({ financials }: { financials: FinancialStatement }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <FileText className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      Financial Statements
    </h3>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Revenue</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${(financials.revenue / 1000000000).toFixed(2)}B
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Net Income</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            ${(financials.net_income / 1000000000).toFixed(2)}B
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Gross Margin</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {financials.gross_margin.toFixed(2)}%
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Operating Margin</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {financials.operating_margin.toFixed(2)}%
          </p>
        </div>
      </div>
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Net Margin</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {financials.net_margin.toFixed(2)}%
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>ROE</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {(financials.roe * 100).toFixed(2)}%
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>ROA</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {(financials.roa * 100).toFixed(2)}%
          </p>
        </div>
        <div>
          <label className="text-sm font-medium" style={{ color: DARK_THEME.colors.textSecondary }}>Current Ratio</label>
          <p className="text-lg font-semibold" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
            {financials.current_ratio.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  </DarkCard>
);

const TradingViewChart = ({ data, symbol }: { data: ChartData[]; symbol: string }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <BarChart3 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      {symbol} Chart
    </h3>
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={DARK_THEME.colors.primary} stopOpacity={0.8} />
              <stop offset="95%" stopColor={DARK_THEME.colors.primary} stopOpacity={0.2} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={DARK_THEME.colors.borderDefault} />
          <XAxis
            dataKey="timestamp"
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
            formatter={(value: any, name: any) => [
              <div key="name" style={{ color: DARK_THEME.colors.textSecondary }}>
                {name}
              </div>,
              <div key="value" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
                ${typeof value === 'number' ? value.toFixed(2) : value}
              </div>
            ]}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke={DARK_THEME.colors.primary}
            strokeWidth={2}
            fill="url(#colorGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  </DarkCard>
);

const CandlestickChart = ({ data, symbol }: { data: ChartData[]; symbol: string }) => (
  <DarkCard className="p-6">
    <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ color: DARK_THEME.colors.textPrimary }}>
      <BarChart3 className="w-5 h-5" style={{ color: DARK_THEME.colors.primary }} />
      {symbol} Candlestick Chart
    </h3>
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke={DARK_THEME.colors.borderDefault} />
          <XAxis
            dataKey="timestamp"
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
            formatter={(value: any, name: any) => [
              <div key="name" style={{ color: DARK_THEME.colors.textSecondary }}>
                {name}
              </div>,
              <div key="value" style={{ color: DARK_THEME.colors.textPrimary, fontFamily: 'monospace' }}>
                ${typeof value === 'number' ? value.toFixed(2) : value}
              </div>
            ]}
          />
          <Bar dataKey="high" fill={DARK_THEME.colors.success} />
          <Bar dataKey="low" fill={DARK_THEME.colors.danger} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  </DarkCard>
);

// Main Component
export default function AdvancedStockAnalysis({ symbol }: { symbol: string }) {
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [financialStatements, setFinancialStatements] = useState<FinancialStatement | null>(null);
  const [technicalIndicators, setTechnicalIndicators] = useState<TechnicalIndicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<'area' | 'candlestick'>('area');

  useEffect(() => {
    const fetchAdvancedData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all data from the advanced API
        const [chartResponse, profileResponse, financialsResponse, indicatorsResponse] = await Promise.all([
          fetch(`/api/advanced/charts/${symbol}`).then(r => r.json()),
          fetch(`/api/advanced/company/${symbol}`).then(r => r.json()),
          fetch(`/api/advanced/company/${symbol}/financials`).then(r => r.json()),
          fetch(`/api/advanced/company/${symbol}/indicators?indicators=RSI,MACD,Bollinger,SMA,EMA`).then(r => r.json()),
        ]);

        // Process chart data
        if (chartResponse.chart_data && chartResponse.chart_data.candlestick) {
          const processedData = chartResponse.chart_data.candlestick.map((item: any) => ({
            timestamp: new Date(item.time).toLocaleDateString(),
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
            volume: item.volume,
          }));
          setChartData(processedData);
        }

        // Process company profile
        if (profileResponse.company_data && profileResponse.company_data.profile) {
          setCompanyProfile(profileResponse.company_data.profile);
        }

        // Process financial statements
        if (financialsResponse.financials) {
          setFinancialStatements(financialsResponse.financials);
        }

        // Process technical indicators
        if (indicatorsResponse.indicators_data) {
          const indicators = Object.entries(indicatorsResponse.indicators_data).map(([name, data]: [string, any]) => ({
            name,
            value: data.value || 0,
            signal: data.signal || 'neutral',
            color: data.signal === 'buy' ? DARK_THEME.colors.success :
              data.signal === 'sell' ? DARK_THEME.colors.danger :
                DARK_THEME.colors.warning,
          }));
          setTechnicalIndicators(indicators);
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchAdvancedData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-t-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: DARK_THEME.colors.textSecondary }}>Loading advanced stock analysis...</p>
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
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold" style={{ color: DARK_THEME.colors.textPrimary }}>
            {symbol} Advanced Analysis
          </h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setChartType('area')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${chartType === 'area'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              Area Chart
            </button>
            <button
              onClick={() => setChartType('candlestick')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${chartType === 'candlestick'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              Candlestick
            </button>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Charts */}
          <div className="space-y-6">
            {chartType === 'area' ? (
              <TradingViewChart data={chartData} symbol={symbol} />
            ) : (
              <CandlestickChart data={chartData} symbol={symbol} />
            )}

            {technicalIndicators.length > 0 && (
              <TechnicalIndicatorsPanel indicators={technicalIndicators} />
            )}
          </div>

          {/* Right Column - Company Info */}
          <div className="space-y-6">
            {companyProfile && (
              <CompanyProfileCard profile={companyProfile} />
            )}

            {financialStatements && (
              <FinancialStatementsCard financials={financialStatements} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
