from app.services.market_service import MarketService

service = MarketService()
print("TCS in TRACKED_STOCKS:", any(stock['ticker'] == 'TCS' for stock in service.TRACKED_STOCKS))
print("All tickers with TCS:", [stock['ticker'] for stock in service.TRACKED_STOCKS if 'TCS' in stock['ticker']])
