import React, { useState, useEffect } from 'react';
import { unifiedAPI } from '@/api/unified';
import { cn } from '@/utils/cn';
import { Activity, CheckCircle, AlertCircle, Clock, Globe, TrendingUp, TrendingDown, Zap, Info } from 'lucide-react';

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
  }
};

interface APIStatus {
  endpoint: string;
  status: 'loading' | 'success' | 'error';
  responseTime?: number;
  error?: string;
  data?: any;
}

interface DataSource {
  name: string;
  status: 'active' | 'inactive' | 'error';
  endpoint: string;
  lastChecked: string;
}

export default function FinanceAPIDashboard() {
  const [apiStatuses, setApiStatuses] = useState<Record<string, APIStatus>>({});
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const testEndpoints = [
    { name: 'US Stock (AAPL)', endpoint: '/api/google-finance/quote/AAPL/NASDAQ' },
    { name: 'Indian Stock (RELIANCE)', endpoint: '/api/google-finance/quote/RELIANCE.NS/NSE' },
    { name: 'Market Indexes', endpoint: '/api/google-finance/market/indexes' },
    { name: 'US Gainers', endpoint: '/api/google-finance/market/gainers' },
    { name: 'NSE Gainers', endpoint: '/api/google-finance/market/nse-gainers' },
    { name: 'Crypto', endpoint: '/api/google-finance/market/crypto' },
  ];

  const checkAPIHealth = async () => {
    setIsRefreshing(true);
    const newStatuses: Record<string, APIStatus> = {};
    const sources: DataSource[] = [];

    for (const test of testEndpoints) {
      const startTime = Date.now();
      try {
        const response = await fetch(`http://localhost:8000${test.endpoint}`);
        const responseTime = Date.now() - startTime;
        const data = await response.json();

        newStatuses[test.name] = {
          endpoint: test.endpoint,
          status: response.ok ? 'success' : 'error',
          responseTime,
          data: response.ok ? data : null,
          error: response.ok ? undefined : `HTTP ${response.status}`
        };

        // Extract data source information
        if (response.ok && data?.source) {
          const existingSource = sources.find(s => s.name === data.source);
          if (!existingSource) {
            sources.push({
              name: data.source,
              status: 'active',
              endpoint: test.endpoint,
              lastChecked: new Date().toLocaleTimeString()
            });
          }
        }
      } catch (error) {
        newStatuses[test.name] = {
          endpoint: test.endpoint,
          status: 'error',
          responseTime: Date.now() - startTime,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    }

    setApiStatuses(newStatuses);
    setDataSources(sources);
    setIsRefreshing(false);
  };

  useEffect(() => {
    checkAPIHealth();
    const interval = setInterval(checkAPIHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4" style={{ color: DARK_THEME.colors.success }} />;
      case 'error':
        return <AlertCircle className="w-4 h-4" style={{ color: DARK_THEME.colors.danger }} />;
      case 'loading':
        return <Activity className="w-4 h-4 animate-spin" style={{ color: DARK_THEME.colors.primary }} />;
      default:
        return <Clock className="w-4 h-4" style={{ color: DARK_THEME.colors.textMuted }} />;
    }
  };

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

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
              Finance API Dashboard
            </h1>
            <p className="text-sm" style={{ color: DARK_THEME.colors.textSecondary }}>
              Real-time API status and data source monitoring
            </p>
          </div>
          <button
            onClick={checkAPIHealth}
            disabled={isRefreshing}
            className="px-4 py-2 rounded-xl font-medium text-sm transition-all flex items-center gap-2"
            style={{
              backgroundColor: DARK_THEME.colors.primary,
              color: DARK_THEME.colors.textPrimary,
              boxShadow: DARK_THEME.shadows.card,
            }}
          >
            <Activity className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
            {isRefreshing ? 'Checking...' : 'Refresh'}
          </button>
        </div>

        {/* API Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {Object.entries(apiStatuses).map(([name, status]) => (
            <div
              key={name}
              className="p-4 rounded-2xl border transition-all"
              style={{
                backgroundColor: DARK_THEME.colors.bgCard,
                borderColor: status.status === 'success' ? DARK_THEME.colors.success + '40' :
                           status.status === 'error' ? DARK_THEME.colors.danger + '40' :
                           DARK_THEME.colors.borderDefault,
                boxShadow: DARK_THEME.shadows.card,
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-sm mb-1" style={{ color: DARK_THEME.colors.textPrimary }}>
                    {name}
                  </h3>
                  <p className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                    {status.endpoint}
                  </p>
                </div>
                {getStatusIcon(status.status)}
              </div>
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {status.responseTime && (
                    <>
                      <Clock className="w-3 h-3" style={{ color: DARK_THEME.colors.textMuted }} />
                      <span style={{ color: DARK_THEME.colors.textSecondary }}>
                        {status.responseTime}ms
                      </span>
                    </>
                  )}
                </div>
                {status.data?.source && (
                  <div className="flex items-center gap-1 px-2 py-1 rounded"
                    style={{
                      backgroundColor: `${getDataSourceColor(status.data.source)}20`,
                      color: getDataSourceColor(status.data.source),
                    }}
                  >
                    <span>{getDataSourceIcon(status.data.source)}</span>
                    <span>{status.data.source}</span>
                  </div>
                )}
              </div>
              
              {status.error && (
                <p className="text-xs mt-2" style={{ color: DARK_THEME.colors.danger }}>
                  {status.error}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Data Sources Summary */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4" style={{ color: DARK_THEME.colors.textPrimary }}>
            Active Data Sources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dataSources.map((source) => (
              <div
                key={source.name}
                className="p-4 rounded-2xl border flex items-center gap-3"
                style={{
                  backgroundColor: DARK_THEME.colors.bgCard,
                  borderColor: DARK_THEME.colors.borderDefault,
                  boxShadow: DARK_THEME.shadows.card,
                }}
              >
                <div className="text-2xl">
                  {getDataSourceIcon(source.name)}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-sm" style={{ color: DARK_THEME.colors.textPrimary }}>
                    {source.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h3>
                  <p className="text-xs" style={{ color: DARK_THEME.colors.textMuted }}>
                    Last checked: {source.lastChecked}
                  </p>
                </div>
                <CheckCircle className="w-5 h-5" style={{ color: DARK_THEME.colors.success }} />
              </div>
            ))}
          </div>
        </div>

        {/* Sample Data Display */}
        <div>
          <h2 className="text-xl font-semibold mb-4" style={{ color: DARK_THEME.colors.textPrimary }}>
            Live Data Samples
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(apiStatuses)
              .filter(([_, status]) => status.status === 'success' && status.data)
              .map(([name, status]) => (
                <div
                  key={name}
                  className="p-4 rounded-2xl border"
                  style={{
                    backgroundColor: DARK_THEME.colors.bgCard,
                    borderColor: DARK_THEME.colors.borderDefault,
                    boxShadow: DARK_THEME.shadows.card,
                  }}
                >
                  <h3 className="font-semibold text-sm mb-2" style={{ color: DARK_THEME.colors.textPrimary }}>
                    {name}
                  </h3>
                  <pre className="text-xs overflow-auto" style={{ 
                    color: DARK_THEME.colors.textSecondary,
                    maxHeight: '150px'
                  }}>
                    {JSON.stringify(status.data, null, 2)}
                  </pre>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
