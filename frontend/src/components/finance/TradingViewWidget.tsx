import React, { useEffect, useRef, memo } from 'react';

export type TradingViewWidgetType = 
  | 'AdvancedChart' 
  | 'TickerTape' 
  | 'MarketSummary' 
  | 'EconomicCalendar' 
  | 'SymbolInfo' 
  | 'TechnicalAnalysis' 
  | 'StockHeatmap'
  | 'CryptoHeatmap';

interface Props {
  type: TradingViewWidgetType;
  symbol?: string;
  height?: string | number;
  width?: string | number;
  config?: any;
  containerId?: string;
}

const WIDGET_SCRIPTS: Record<TradingViewWidgetType, string> = {
  AdvancedChart: 'https://s3.tradingview.com/tv.js',
  TickerTape: 'https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js',
  MarketSummary: 'https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js',
  EconomicCalendar: 'https://s3.tradingview.com/external-embedding/embed-widget-events.js',
  SymbolInfo: 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js',
  TechnicalAnalysis: 'https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js',
  StockHeatmap: 'https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js',
  CryptoHeatmap: 'https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js',
};

const TradingViewWidget: React.FC<Props> = ({ 
  type, 
  symbol, 
  height = '100%', 
  width = '100%', 
  config = {},
  containerId
}) => {
  const container = useRef<HTMLDivElement>(null);
  const internalId = containerId || `tv-widget-${type}-${Math.random().toString(36).substr(2, 9)}`;

  useEffect(() => {
    if (!container.current) return;

    // Clear previous content
    container.current.innerHTML = '';

    const script = document.createElement('script');
    script.src = WIDGET_SCRIPTS[type];
    script.type = 'text/javascript';
    script.async = true;

    // Special handling for Advanced Chart (Old style API)
    if (type === 'AdvancedChart') {
      const widgetDiv = document.createElement('div');
      widgetDiv.id = internalId;
      widgetDiv.style.height = '100%';
      widgetDiv.style.width = '100%';
      container.current.appendChild(widgetDiv);

      script.onload = () => {
        if (typeof (window as any).TradingView !== 'undefined') {
          new (window as any).TradingView.widget({
            autosize: true,
            symbol: symbol || 'NASDAQ:AAPL',
            interval: 'D',
            timezone: 'Asia/Kolkata',
            theme: 'dark',
            style: '1',
            locale: 'en',
            enable_publishing: false,
            allow_symbol_change: true,
            container_id: internalId,
            hide_top_toolbar: false,
            hide_legend: false,
            save_image: true,
            backgroundColor: 'rgba(10, 11, 15, 0)',
            gridLineColor: 'rgba(255, 255, 255, 0.05)',
            ...config
          });
        }
      };
      document.head.appendChild(script);
    } 
    // Embedded JSON config style (New style API)
    else {
      const widgetContainer = document.createElement('div');
      widgetContainer.className = 'tradingview-widget-container__widget';
      container.current.appendChild(widgetContainer);

      const defaultConfig = {
        colorTheme: 'dark',
        isTransparent: true,
        displayMode: 'adaptive',
        locale: 'en',
        width: '100%',
        height: height === '100%' ? 400 : height,
        symbol: symbol,
        ...config
      };

      script.innerHTML = JSON.stringify(defaultConfig);
      container.current.appendChild(script);
    }

    return () => {
      // Cleanup happens via innerHTML = '' on next effect run
      // but we should technically remove scripts if they were added to head
      if (type === 'AdvancedChart') {
        const headScripts = document.head.getElementsByTagName('script');
        for (let i = 0; i < headScripts.length; i++) {
          if (headScripts[i].src === WIDGET_SCRIPTS[type]) {
            // document.head.removeChild(headScripts[i]); 
            // Often safer to leave it if multiple widgets use it, 
            // but TV.js is global.
          }
        }
      }
    };
  }, [type, symbol, height, width, JSON.stringify(config)]);

  return (
    <div 
      ref={container} 
      className="tradingview-widget-container" 
      style={{ height, width, overflow: 'hidden' }}
    />
  );
};

export default memo(TradingViewWidget);
