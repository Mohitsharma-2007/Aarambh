import { useState, useEffect } from 'react';
import { Check, X, RefreshCw, Settings, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import unifiedDataService from '@/services/unifiedDataService';

interface ProviderConfig {
  news: 'serpapi' | 'newsplatform' | 'both';
  finance: 'serpapi' | 'financeapi' | 'both';
  economy: 'economyplatform' | 'serpapi' | 'both';
}

interface ProviderStatus {
  id: string;
  name: string;
  healthy: boolean;
  lastChecked?: Date;
  priority: number;
}

export default function ProviderSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState<ProviderConfig>(() => {
    const saved = localStorage.getItem('provider-config');
    return saved ? JSON.parse(saved) : {
      news: 'both',
      finance: 'both',
      economy: 'economyplatform',
    };
  });
  const [providerStatus, setProviderStatus] = useState<Record<string, ProviderStatus>>({});
  const [testing, setTesting] = useState<string | null>(null);

  // Load provider status on mount
  useEffect(() => {
    updateProviderStatus();
    const interval = setInterval(updateProviderStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const updateProviderStatus = async () => {
    await unifiedDataService.refreshAllProviders();
    const status = unifiedDataService.getProviderStatus();
    
    const providers = [
      { id: 'serpapi', name: 'SerpAPI (Google)', priority: 1 },
      { id: 'newsplatform', name: 'News Platform', priority: 2 },
      { id: 'financeapi', name: 'Finance API', priority: 2 },
      { id: 'economyplatform', name: 'Economy Platform', priority: 1 },
    ];

    const statusMap: Record<string, ProviderStatus> = {};
    providers.forEach(provider => {
      statusMap[provider.id] = {
        ...provider,
        healthy: status[provider.id] || false,
        lastChecked: new Date(),
      };
    });

    setProviderStatus(statusMap);
  };

  const testProvider = async (providerId: string) => {
    setTesting(providerId);
    try {
      const isHealthy = await unifiedDataService.checkProviderHealth(providerId);
      setProviderStatus(prev => ({
        ...prev,
        [providerId]: {
          ...prev[providerId],
          healthy: isHealthy,
          lastChecked: new Date(),
        },
      }));
    } catch (error) {
      console.error(`Failed to test ${providerId}:`, error);
    } finally {
      setTesting(null);
    }
  };

  const saveConfig = (newConfig: ProviderConfig) => {
    setConfig(newConfig);
    localStorage.setItem('provider-config', JSON.stringify(newConfig));
  };

  const getProviderHealthColor = (healthy: boolean) => {
    return healthy ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  const getProviderHealthIcon = (healthy: boolean) => {
    return healthy ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />;
  };

  return (
    <div className="relative">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Settings className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">Data Sources</span>
        <div className="flex gap-1">
          {Object.values(providerStatus).filter(p => p.healthy).length > 0 && (
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          )}
          {Object.values(providerStatus).filter(p => !p.healthy).length > 0 && (
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
          )}
        </div>
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Panel */}
          <div className="fixed top-16 right-4 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[80vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Data Provider Configuration</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            {/* Provider Status */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">Provider Status</h4>
                <button
                  onClick={updateProviderStatus}
                  className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Refresh All
                </button>
              </div>
              
              <div className="space-y-2">
                {Object.values(providerStatus).map(provider => (
                  <div
                    key={provider.id}
                    className={cn(
                      "flex items-center justify-between p-2 rounded-lg border",
                      getProviderHealthColor(provider.healthy)
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {getProviderHealthIcon(provider.healthy)}
                      <div>
                        <div className="text-sm font-medium">{provider.name}</div>
                        <div className="text-xs opacity-75">Priority: {provider.priority}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {provider.lastChecked && (
                        <span className="text-xs opacity-75">
                          {provider.lastChecked.toLocaleTimeString()}
                        </span>
                      )}
                      <button
                        onClick={() => testProvider(provider.id)}
                        disabled={testing === provider.id}
                        className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                      >
                        {testing === provider.id ? 'Testing...' : 'Test'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Configuration */}
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-4">Provider Preferences</h4>
              
              <div className="space-y-4">
                {/* News Provider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    News Data Source
                  </label>
                  <select
                    value={config.news}
                    onChange={(e) => saveConfig({ ...config, news: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="serpapi">SerpAPI (Google News)</option>
                    <option value="newsplatform">News Platform (RSS Feeds)</option>
                    <option value="both">Both (SerpAPI Primary)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Choose primary source for news data
                  </p>
                </div>

                {/* Finance Provider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Finance Data Source
                  </label>
                  <select
                    value={config.finance}
                    onChange={(e) => saveConfig({ ...config, finance: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="serpapi">SerpAPI (Google Finance)</option>
                    <option value="financeapi">Finance API (Scrapers)</option>
                    <option value="both">Both (SerpAPI Primary)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Choose primary source for finance data
                  </p>
                </div>

                {/* Economy Provider */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Economy Data Source
                  </label>
                  <select
                    value={config.economy}
                    onChange={(e) => saveConfig({ ...config, economy: e.target.value as any })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="economyplatform">Economy Platform (Gov Data)</option>
                    <option value="serpapi">SerpAPI (Google)</option>
                    <option value="both">Both (Economy Platform Primary)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Choose primary source for economy data
                  </p>
                </div>
              </div>
            </div>

            {/* Info Section */}
            <div className="p-4 bg-gray-50 border-t border-gray-200">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-xs text-gray-600">
                  <p className="font-medium mb-1">How it works:</p>
                  <ul className="space-y-1">
                    <li>• Primary provider is used first</li>
                    <li>• Automatic fallback to secondary providers</li>
                    <li>• Health checks prevent failed requests</li>
                    <li>• Responses are cached for performance</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
