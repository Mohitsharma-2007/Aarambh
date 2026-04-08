import { useRef, useEffect, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { api } from '@/api'
import { Loader2, X, TrendingUp, TrendingDown, BarChart3, DollarSign, Package } from 'lucide-react'

interface StockData {
  ticker: string
  name: string
  sector: string
  industry: string
  marketCap: number
  priceChange: number
  price: number
  volume?: number
  high52w?: number
  low52w?: number
}

interface HistoricalPoint {
  date: string
  price: number
  volume: number
}

type TimePeriod = '1D' | '1W' | '1M' | '6M' | 'YTD' | '1Y'

interface MarketHeatmapProps {
  height?: number
  onStockClick?: (ticker: string) => void
}

export default function MarketHeatmap({ height = 600, onStockClick }: MarketHeatmapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const chartRef = useRef<SVGSVGElement>(null)
  const [stocks, setStocks] = useState<StockData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null)
  const [hoveredStock, setHoveredStock] = useState<StockData | null>(null)
  const [hoveredSector, setHoveredSector] = useState<string | null>(null)
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 })
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('1D')
  const [historicalData, setHistoricalData] = useState<HistoricalPoint[]>([])
  const [historicalLoading, setHistoricalLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)

  // Fetch market data from API
  useEffect(() => {
    async function fetchMarketData() {
      try {
        setLoading(true)
        setError(null)
        const result = await api.getMarketHeatmap()
        const data = result?.data || []
        if (data.length > 0) {
          setStocks(data)
        } else {
          setError('No market data available')
        }
      } catch (err) {
        console.error('Failed to fetch market data:', err)
        setError('Failed to load market data. Please check if the backend is running.')
      } finally {
        setLoading(false)
      }
    }
    fetchMarketData()
  }, [])

  // Fetch historical data from API when stock or period changes
  useEffect(() => {
    async function fetchHistoricalData() {
      if (!selectedStock) return
      
      try {
        setHistoricalLoading(true)
        const data = await api.getStockHistory(selectedStock.ticker, timePeriod)
        if (data && data.length > 0) {
          setHistoricalData(data)
        } else {
          // Generate placeholder data if API returns empty
          setHistoricalData(generatePlaceholderData(timePeriod, selectedStock.price))
        }
      } catch (err) {
        console.warn('Historical data not available, using placeholder:', err)
        setHistoricalData(generatePlaceholderData(timePeriod, selectedStock.price))
      } finally {
        setHistoricalLoading(false)
      }
    }
    fetchHistoricalData()
  }, [selectedStock, timePeriod])

  // Generate placeholder data when API is unavailable
  function generatePlaceholderData(period: TimePeriod, basePrice: number): HistoricalPoint[] {
    const now = new Date()
    const points: HistoricalPoint[] = []
    
    let days = 1
    switch (period) {
      case '1D': days = 1; break
      case '1W': days = 7; break
      case '1M': days = 30; break
      case '6M': days = 180; break
      case 'YTD': days = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / (1000 * 60 * 60 * 24)); break
      case '1Y': days = 365; break
    }
    
    for (let d = days; d >= 0; d--) {
      const date = new Date(now)
      date.setDate(date.getDate() - d)
      const trend = Math.random() > 0.48 ? 1 : -1
      const change = trend * Math.random() * 0.02 * basePrice
      basePrice = basePrice + change
      points.push({
        date: date.toISOString(),
        price: basePrice,
        volume: Math.floor(Math.random() * 50000000) + 5000000,
      })
    }
    
    return points
  }

  // Draw chart in modal
  useEffect(() => {
    if (!chartRef.current || !showModal || historicalData.length === 0) return

    const svg = d3.select(chartRef.current)
    const width = chartRef.current.clientWidth
    const height = 200
    const margin = { top: 20, right: 20, bottom: 30, left: 50 }

    svg.selectAll('*').remove()

    const x = d3.scaleTime()
      .domain(d3.extent(historicalData, d => new Date(d.date)) as [Date, Date])
      .range([margin.left, width - margin.right])

    const y = d3.scaleLinear()
      .domain([
        d3.min(historicalData, d => d.price) as number * 0.98,
        d3.max(historicalData, d => d.price) as number * 1.02
      ])
      .range([height - margin.bottom, margin.top])

    // Line
    const line = d3.line<HistoricalPoint>()
      .x(d => x(new Date(d.date)))
      .y(d => y(d.price))

    const g = svg.append('g')

    // Grid lines
    g.append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .attr('color', '#374151')
      .call(d3.axisBottom(x).ticks(5).tickFormat(d3.timeFormat('%b %d') as any))

    g.append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .attr('color', '#374151')
      .call(d3.axisLeft(y).ticks(4).tickFormat((d: any) => `$${d.toFixed(0)}`))

    // Area gradient
    const area = d3.area<HistoricalPoint>()
      .x(d => x(new Date(d.date)))
      .y0(height - margin.bottom)
      .y1(d => y(d.price))

    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'areaGradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', selectedStock && selectedStock.priceChange >= 0 ? '#22c55e' : '#ef4444')
      .attr('stop-opacity', 0.3)

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', selectedStock && selectedStock.priceChange >= 0 ? '#22c55e' : '#ef4444')
      .attr('stop-opacity', 0)

    g.append('path')
      .datum(historicalData)
      .attr('fill', 'url(#areaGradient)')
      .attr('d', area)

    // Line path
    g.append('path')
      .datum(historicalData)
      .attr('fill', 'none')
      .attr('stroke', selectedStock && selectedStock.priceChange >= 0 ? '#22c55e' : '#ef4444')
      .attr('stroke-width', 2)
      .attr('d', line)

  }, [historicalData, showModal, selectedStock])

  // Get color based on price change
  const getColor = useCallback((change: number) => {
    if (change >= 3) return '#15803d'
    if (change >= 1.5) return '#22c55e'
    if (change >= 0.5) return '#4ade80'
    if (change >= 0) return '#86efac'
    if (change >= -0.5) return '#fca5a5'
    if (change >= -1.5) return '#ef4444'
    if (change >= -3) return '#dc2626'
    return '#991b1b'
  }, [])

  // Build treemap hierarchy
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || loading) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    d3.select(svgRef.current).selectAll('*').remove()

    const sectorMap = new Map<string, StockData[]>()
    stocks.forEach(stock => {
      const sector = stock.sector
      if (!sectorMap.has(sector)) {
        sectorMap.set(sector, [])
      }
      sectorMap.get(sector)!.push(stock)
    })

    const rootData = {
      name: 'Market',
      children: Array.from(sectorMap.entries()).map(([sector, stocks]) => ({
        name: sector,
        children: stocks.map(stock => ({
          ...stock,
          value: stock.marketCap,
        })),
      })),
    }

    const root = d3.hierarchy(rootData)
      .sum(d => (d as any).value || 0)
      .sort((a, b) => ((b.value || 0) - (a.value || 0)))

    const treemap = d3.treemap<any>()
      .size([width, height])
      .paddingOuter(3)
      .paddingInner(1)
      .round(true)

    treemap(root)

    const svg = d3.select(svgRef.current)

    const cell = svg.selectAll('g')
      .data(root.leaves())
      .join('g')
      .attr('transform', d => `translate(${(d as any).x0},${(d as any).y0})`)

    cell.append('rect')
      .attr('width', d => Math.max(0, (d as any).x1 - (d as any).x0))
      .attr('height', d => Math.max(0, (d as any).y1 - (d as any).y0))
      .attr('fill', d => getColor((d.data as any).priceChange))
      .attr('stroke', '#1a1a2e')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('click', (_event, d) => {
        const stock = d.data as any as StockData
        setSelectedStock(stock)
        setShowModal(true)
        onStockClick?.(stock.ticker)
      })
      .on('mouseover', function(event, d) {
        d3.select(this).attr('stroke', '#ffffff').attr('stroke-width', 2)
        setHoveredStock(d.data as any as StockData)
        setHoveredSector((d.data as any).sector)
        // Get cursor position relative to container
        const rect = container.getBoundingClientRect()
        setTooltipPos({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top
        })
      })
      .on('mousemove', function(event) {
        // Update tooltip position on mouse move
        const rect = container.getBoundingClientRect()
        setTooltipPos({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top
        })
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke', '#1a1a2e').attr('stroke-width', 1)
        setHoveredStock(null)
        setHoveredSector(null)
      })

    cell.append('text')
      .text(d => (d.data as any).ticker)
      .attr('x', 4)
      .attr('y', 14)
      .attr('font-size', d => {
        const w = (d as any).x1 - (d as any).x0
        const h = (d as any).y1 - (d as any).y0
        if (w < 40 || h < 30) return '8px'
        if (w < 60 || h < 40) return '10px'
        return '12px'
      })
      .attr('font-weight', '600')
      .attr('fill', '#ffffff')
      .attr('font-family', 'IBM Plex Mono, monospace')

    cell.append('text')
      .text(d => {
        const change = (d.data as any).priceChange
        return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`
      })
      .attr('x', 4)
      .attr('y', 26)
      .attr('font-size', d => {
        const w = (d as any).x1 - (d as any).x0
        const h = (d as any).y1 - (d as any).y0
        if (w < 50 || h < 40) return '7px'
        return '9px'
      })
      .attr('fill', '#ffffff')
      .attr('opacity', 0.9)
      .attr('font-family', 'IBM Plex Mono, monospace')

  }, [stocks, loading, getColor, onStockClick])

  const formatMarketCap = (cap: number) => {
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`
    return `$${(cap / 1e6).toFixed(2)}M`
  }

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(2)}B`
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}M`
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(2)}K`
    return vol.toString()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-data font-semibold text-text-primary tracking-wide">
            MARKET HEATMAP
          </h2>
          <p className="text-xs text-text-muted mt-1">
            Size: Market Cap · Color: Price Change
          </p>
        </div>
        
        {/* Time Period Toggle */}
        <div className="flex bg-bg-secondary border border-border-subtle rounded-lg p-0.5">
          {(['1D', '1W', '1M', '6M', 'YTD', '1Y'] as TimePeriod[]).map((period) => (
            <button
              key={period}
              onClick={() => setTimePeriod(period)}
              className={`px-3 py-1 text-xs font-data rounded transition-colors ${
                timePeriod === period
                  ? 'bg-accent text-bg-primary'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* Heatmap */}
      <div 
        ref={containerRef} 
        className="flex-1 relative bg-bg-secondary rounded-lg border border-border-subtle overflow-hidden"
        style={{ minHeight: height }}
      >
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 animate-spin text-accent" />
          </div>
        ) : (
          <svg ref={svgRef} className="w-full h-full" />
        )}

        {/* Hover Tooltip - follows cursor */}
        {hoveredStock && !showModal && (
          <div 
            className="absolute pointer-events-none z-10"
            style={{ 
              left: tooltipPos.x + 15,
              top: tooltipPos.y + 15,
              transform: tooltipPos.x > (containerRef.current?.clientWidth || 0) - 280 ? 'translateX(-100%)' : 'none'
            }}
          >
            <div className="bg-bg-secondary/75 backdrop-blur-sm border border-border-subtle/50 rounded-lg p-3 min-w-56 shadow-xl">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-data font-bold text-text-primary">
                  {hoveredStock.ticker}
                </span>
                <span 
                  className="flex items-center gap-1 text-sm font-data font-semibold"
                  style={{ color: getColor(hoveredStock.priceChange) }}
                >
                  {hoveredStock.priceChange >= 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {hoveredStock.priceChange >= 0 ? '+' : ''}{hoveredStock.priceChange.toFixed(2)}%
                </span>
              </div>
              
              <div className="text-xs text-text-primary/80 font-medium mb-2">{hoveredStock.name}</div>
              
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-text-muted/70 w-16">Sector</span>
                  <span className="text-text-secondary/90">{hoveredStock.sector}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-text-muted/70 w-16">Industry</span>
                  <span className="text-text-secondary/90">{hoveredStock.industry}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-text-muted/70 w-16">Price</span>
                  <span className="text-text-secondary/90">${hoveredStock.price.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-text-muted/70 w-16">Market Cap</span>
                  <span className="text-text-secondary/90">{formatMarketCap(hoveredStock.marketCap)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-text-muted/70 w-16">Volume</span>
                  <span className="text-text-secondary/90">{formatVolume(hoveredStock.volume || 0)}</span>
                </div>
              </div>
              
              <div className="mt-2 pt-1.5 border-t border-border-subtle/30 text-[10px] text-text-muted/60">
                Click for detailed view
              </div>
            </div>
          </div>
        )}

        {/* Sector Summary on Hover */}
        {hoveredSector && !hoveredStock && (
          <div className="absolute bottom-4 left-4 bg-bg-secondary/95 border border-border-subtle rounded-lg p-3">
            <div className="text-xs font-data text-text-primary">{hoveredSector}</div>
          </div>
        )}
      </div>

      {/* Color Legend */}
      <div className="flex items-center justify-center gap-1 mt-3">
        <span className="text-xs text-text-muted">-5%</span>
        <div className="flex h-3 rounded overflow-hidden">
          <div className="w-6 bg-red-900" />
          <div className="w-6 bg-red-700" />
          <div className="w-6 bg-red-500" />
          <div className="w-6 bg-red-300" />
          <div className="w-6 bg-green-300" />
          <div className="w-6 bg-green-500" />
          <div className="w-6 bg-green-700" />
          <div className="w-6 bg-green-900" />
        </div>
        <span className="text-xs text-text-muted">+5%</span>
      </div>

      {/* Detail Modal */}
      {showModal && selectedStock && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <div 
            className="bg-bg-secondary border border-border-subtle rounded-lg p-6 w-[600px] max-h-[80vh] overflow-auto"
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-xl font-data font-bold text-text-primary">
                    {selectedStock.ticker}
                  </span>
                  <span 
                    className="flex items-center gap-1 px-2 py-0.5 rounded text-sm font-data font-semibold"
                    style={{ 
                      color: getColor(selectedStock.priceChange),
                      backgroundColor: `${getColor(selectedStock.priceChange)}20`
                    }}
                  >
                    {selectedStock.priceChange >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    {selectedStock.priceChange >= 0 ? '+' : ''}{selectedStock.priceChange.toFixed(2)}%
                  </span>
                </div>
                <div className="text-sm text-text-muted mt-1">{selectedStock.name}</div>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-bg-tertiary rounded transition-colors"
              >
                <X className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            {/* Time Period Toggle in Modal */}
            <div className="flex bg-bg-tertiary rounded-lg p-0.5 mb-4 w-fit">
              {(['1D', '1W', '1M', '6M', 'YTD', '1Y'] as TimePeriod[]).map((period) => (
                <button
                  key={period}
                  onClick={() => setTimePeriod(period)}
                  className={`px-3 py-1 text-xs font-data rounded transition-colors ${
                    timePeriod === period
                      ? 'bg-accent text-bg-primary'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>

            {/* Chart */}
            <div className="bg-bg-tertiary rounded-lg p-4 mb-4">
              <svg ref={chartRef} className="w-full" style={{ height: 200 }} />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
                  <DollarSign className="w-3 h-3" />
                  Price
                </div>
                <div className="text-lg font-data font-semibold text-text-primary">
                  ${selectedStock.price.toFixed(2)}
                </div>
                <div className="text-xs text-text-muted mt-1">
                  52W Range: ${selectedStock.low52w?.toFixed(2)} - ${selectedStock.high52w?.toFixed(2)}
                </div>
              </div>

              <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
                  <BarChart3 className="w-3 h-3" />
                  Market Cap
                </div>
                <div className="text-lg font-data font-semibold text-text-primary">
                  {formatMarketCap(selectedStock.marketCap)}
                </div>
                <div className="text-xs text-text-muted mt-1">
                  Sector: {selectedStock.sector}
                </div>
              </div>

              <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
                  <Package className="w-3 h-3" />
                  Volume
                </div>
                <div className="text-lg font-data font-semibold text-text-primary">
                  {formatVolume(selectedStock.volume || 0)}
                </div>
                <div className="text-xs text-text-muted mt-1">
                  Industry: {selectedStock.industry}
                </div>
              </div>

              <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs text-text-muted mb-2">
                  {selectedStock.priceChange >= 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  Change ({timePeriod})
                </div>
                <div 
                  className="text-lg font-data font-semibold"
                  style={{ color: getColor(selectedStock.priceChange) }}
                >
                  {selectedStock.priceChange >= 0 ? '+' : ''}{selectedStock.priceChange.toFixed(2)}%
                </div>
                <div className="text-xs text-text-muted mt-1">
                  {selectedStock.priceChange >= 0 ? 'Gains' : 'Losses'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
