import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Circle } from 'lucide-react'
import { api } from '@/api'

interface TickerItem {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
}

// Default data when API is unavailable
const DEFAULT_CRYPTO: TickerItem[] = [
  { symbol: 'BTC', name: 'Bitcoin', price: 0, change: 0, changePercent: 0 },
  { symbol: 'ETH', name: 'Ethereum', price: 0, change: 0, changePercent: 0 },
]

const DEFAULT_INDICES: TickerItem[] = [
  { symbol: 'NIFTY50', name: 'Nifty 50', price: 0, change: 0, changePercent: 0 },
  { symbol: 'SENSEX', name: 'BSE Sensex', price: 0, change: 0, changePercent: 0 },
  { symbol: 'SP500', name: 'S&P 500', price: 0, change: 0, changePercent: 0 },
]

// Top stocks to show in ticker
const TICKER_STOCKS = ['AAPL', 'MSFT', 'GOOG', 'NVDA', 'TSLA', 'AMZN', 'META', 'JPM']

export default function MarketTicker() {
  const [stocks, setStocks] = useState<TickerItem[]>([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    // Update time every second
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Fetch market data periodically
  useEffect(() => {
    async function fetchMarketData() {
      try {
        const result = await api.getMarketHeatmap()
        const data = result?.data || []
        if (data.length > 0) {
          // Filter to ticker stocks and format
          const tickerData = data
            .filter((stock: any) => TICKER_STOCKS.includes(stock.ticker))
            .map((stock: any) => ({
              symbol: stock.ticker,
              name: stock.name,
              price: stock.price,
              change: stock.priceChange * stock.price / 100,
              changePercent: stock.priceChange,
            }))
          setStocks(tickerData)
          setConnected(true)
        }
      } catch (err) {
        console.warn('Market data fetch failed:', err)
        setConnected(false)
        // Use default data when API fails
        setStocks([...DEFAULT_CRYPTO, ...DEFAULT_INDICES])
      } finally {
        setLoading(false)
      }
    }

    fetchMarketData()
    const interval = setInterval(fetchMarketData, 30000) // Every 30s
    return () => clearInterval(interval)
  }, [])

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return price.toLocaleString('en-US', { maximumFractionDigits: 0 })
    }
    return price.toFixed(price < 1 ? 2 : 2)
  }

  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : ''
    return `${sign}${changePercent.toFixed(2)}%`
  }

  return (
    <div className="h-8 bg-bg-secondary border-t border-border-subtle flex items-center overflow-hidden">
      {/* Connection Status */}
      <div className="flex items-center gap-2 px-4 border-r border-border-subtle flex-shrink-0">
        <Circle className={`w-2 h-2 ${connected ? 'fill-online' : 'fill-warning'}`} />
        <span className="text-[10px] text-text-muted font-data">
          {connected ? 'CONNECTED' : 'RECONNECTING'}
        </span>
      </div>

      {/* Scrolling Ticker */}
      <div className="flex-1 overflow-hidden">
        <div className="animate-ticker flex items-center gap-6 whitespace-nowrap">
          {/* Stocks from API */}
          {stocks.map((item) => (
            <div key={item.symbol} className="flex items-center gap-2">
              <span className="text-[10px] font-data font-semibold text-text-primary">
                {item.symbol}
              </span>
              <span className="text-[10px] text-text-secondary">
                ${formatPrice(item.price)}
              </span>
              <span className={`flex items-center text-[10px] ${
                item.changePercent >= 0 ? 'text-online' : 'text-accent'
              }`}>
                {item.changePercent >= 0 ? (
                  <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                ) : (
                  <TrendingDown className="w-2.5 h-2.5 mr-0.5" />
                )}
                {formatChange(item.change, item.changePercent)}
              </span>
            </div>
          ))}

          {/* Duplicate for seamless scroll */}
          {stocks.map((item) => (
            <div key={`${item.symbol}-dup`} className="flex items-center gap-2">
              <span className="text-[10px] font-data font-semibold text-text-primary">
                {item.symbol}
              </span>
              <span className="text-[10px] text-text-secondary">
                ${formatPrice(item.price)}
              </span>
              <span className={`flex items-center text-[10px] ${
                item.changePercent >= 0 ? 'text-online' : 'text-accent'
              }`}>
                {item.changePercent >= 0 ? (
                  <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                ) : (
                  <TrendingDown className="w-2.5 h-2.5 mr-0.5" />
                )}
                {formatChange(item.change, item.changePercent)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Time & Version */}
      <div className="flex items-center gap-4 px-4 border-l border-border-subtle flex-shrink-0">
        <span className="text-[10px] text-text-muted font-data">
          {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
        <span className="text-[10px] text-text-muted font-data">
          v1.2.2
        </span>
      </div>

      <style>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker {
          animation: ticker 30s linear infinite;
        }
      `}</style>
    </div>
  )
}
