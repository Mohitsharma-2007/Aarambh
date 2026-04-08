"""
Mock Finance Data API - Temporary solution for frontend testing
Provides sample data for all finance endpoints while fixing the scraping issues
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Sample market data
MOCK_MARKET_DATA = {
    "indexes": {
        "section": "indexes",
        "title": "Market Indexes",
        "count": 6,
        "items": [
            {"name": "S&P 500", "price": "5,123.45", "change": "+0.85%", "ticker": "SPX", "url": ""},
            {"name": "Dow Jones", "price": "39,012.34", "change": "+0.62%", "ticker": "DJI", "url": ""},
            {"name": "Nasdaq", "price": "16,234.56", "change": "+1.23%", "ticker": "IXIC", "url": ""},
            {"name": "NIFTY 50", "price": "19,876.54", "change": "-0.34%", "ticker": "NSEI", "url": ""},
            {"name": "Sensex", "price": "65,432.10", "change": "+0.45%", "ticker": "BSESN", "url": ""},
            {"name": "FTSE 100", "price": "7,654.32", "change": "-0.12%", "ticker": "UKX", "url": ""},
        ]
    },
    "gainers": {
        "section": "gainers",
        "title": "Top Gainers",
        "count": 10,
        "items": [
            {"name": "Apple Inc.", "price": "182.52", "change": "+5.23%", "ticker": "AAPL", "url": ""},
            {"name": "Tesla Inc.", "price": "245.67", "change": "+4.89%", "ticker": "TSLA", "url": ""},
            {"name": "NVIDIA Corp.", "price": "487.31", "change": "+3.76%", "ticker": "NVDA", "url": ""},
            {"name": "Microsoft Corp.", "price": "378.92", "change": "+2.45%", "ticker": "MSFT", "url": ""},
            {"name": "Amazon.com Inc.", "price": "156.78", "change": "+2.12%", "ticker": "AMZN", "url": ""},
            {"name": "Meta Platforms", "price": "312.45", "change": "+1.98%", "ticker": "META", "url": ""},
            {"name": "Alphabet Inc.", "price": "142.67", "change": "+1.87%", "ticker": "GOOGL", "url": ""},
            {"name": "Netflix Inc.", "price": "445.32", "change": "+1.65%", "ticker": "NFLX", "url": ""},
            {"name": "Adobe Inc.", "price": "567.89", "change": "+1.43%", "ticker": "ADBE", "url": ""},
            {"name": "Salesforce Inc.", "price": "234.56", "change": "+1.32%", "ticker": "CRM", "url": ""},
        ]
    },
    "losers": {
        "section": "losers", 
        "title": "Top Losers",
        "count": 10,
        "items": [
            {"name": "Boeing Co.", "price": "198.76", "change": "-3.45%", "ticker": "BA", "url": ""},
            {"name": "Intel Corp.", "price": "34.56", "change": "-2.89%", "ticker": "INTC", "url": ""},
            {"name": "Disney Co.", "price": "89.23", "change": "-2.67%", "ticker": "DIS", "url": ""},
            {"name": "Nike Inc.", "price": "98.45", "change": "-2.34%", "ticker": "NKE", "url": ""},
            {"name": "Coca-Cola Co.", "price": "56.78", "change": "-2.12%", "ticker": "KO", "url": ""},
            {"name": "McDonald's Co.", "price": "267.89", "change": "-1.98%", "ticker": "MCD", "url": ""},
            {"name": "Procter & Gamble", "price": "145.67", "change": "-1.76%", "ticker": "PG", "url": ""},
            {"name": "Johnson & Johnson", "price": "156.78", "change": "-1.54%", "ticker": "JNJ", "url": ""},
            {"name": "Visa Inc.", "price": "234.56", "change": "-1.43%", "ticker": "V", "url": ""},
            {"name": "Mastercard Inc.", "price": "378.90", "change": "-1.32%", "ticker": "MA", "url": ""},
        ]
    },
    "most-active": {
        "section": "most-active",
        "title": "Most Active",
        "count": 10,
        "items": [
            {"name": "Tesla Inc.", "price": "245.67", "change": "+4.89%", "ticker": "TSLA", "url": ""},
            {"name": "Apple Inc.", "price": "182.52", "change": "+5.23%", "ticker": "AAPL", "url": ""},
            {"name": "NVIDIA Corp.", "price": "487.31", "change": "+3.76%", "ticker": "NVDA", "url": ""},
            {"name": "Amazon.com Inc.", "price": "156.78", "change": "+2.12%", "ticker": "AMZN", "url": ""},
            {"name": "Microsoft Corp.", "price": "378.92", "change": "+2.45%", "ticker": "MSFT", "url": ""},
            {"name": "Meta Platforms", "price": "312.45", "change": "+1.98%", "ticker": "META", "url": ""},
            {"name": "Alphabet Inc.", "price": "142.67", "change": "+1.87%", "ticker": "GOOGL", "url": ""},
            {"name": "Bank of America", "price": "34.56", "change": "-0.89%", "ticker": "BAC", "url": ""},
            {"name": "Ford Motor Co.", "price": "12.34", "change": "+1.23%", "ticker": "F", "url": ""},
            {"name": "General Motors", "price": "38.76", "change": "-0.67%", "ticker": "GM", "url": ""},
        ]
    },
    "crypto": {
        "section": "crypto",
        "title": "Cryptocurrency",
        "count": 8,
        "items": [
            {"name": "Bitcoin", "price": "45,678.90", "change": "+2.34%", "ticker": "BTC", "url": ""},
            {"name": "Ethereum", "price": "2,456.78", "change": "+1.89%", "ticker": "ETH", "url": ""},
            {"name": "Binance Coin", "price": "345.67", "change": "-0.45%", "ticker": "BNB", "url": ""},
            {"name": "Cardano", "price": "0.567", "change": "+3.21%", "ticker": "ADA", "url": ""},
            {"name": "Solana", "price": "98.76", "change": "+4.56%", "ticker": "SOL", "url": ""},
            {"name": "Ripple", "price": "0.623", "change": "-1.23%", "ticker": "XRP", "url": ""},
            {"name": "Polkadot", "price": "7.89", "change": "+2.34%", "ticker": "DOT", "url": ""},
            {"name": "Dogecoin", "price": "0.0876", "change": "+5.67%", "ticker": "DOGE", "url": ""},
        ]
    }
}

# Sample stock quotes
MOCK_QUOTES = {
    "AAPL": {
        "ticker": "AAPL",
        "exchange": "NASDAQ", 
        "company_name": "Apple Inc.",
        "price": "182.52",
        "change": "+9.45",
        "change_percent": "+5.23%",
        "currency": "USD",
        "prev_close": "173.07",
        "after_hours": "181.90",
        "key_stats": {
            "Market Cap": "2.89T",
            "P/E Ratio": "29.4",
            "52W High": "199.62",
            "52W Low": "164.08",
            "Volume": "52.3M",
            "Avg Volume": "65.2M",
            "Dividend": "0.96",
            "Yield": "0.53%"
        },
        "about": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, Mac, iPad, and Wearables, Home and Accessories products.",
        "news": [
            {"headline": "Apple Unveils New AI Features for iPhone", "source": "TechCrunch", "url": "https://techcrunch.com/apple-ai"},
            {"headline": "Apple Stock Hits New High After Earnings Beat", "source": "Reuters", "url": "https://reuters.com/apple-stock"},
            {"headline": "Apple Vision Pro Sales Exceed Expectations", "source": "Bloomberg", "url": "https://bloomberg.com/apple-vision"}
        ]
    },
    "TSLA": {
        "ticker": "TSLA",
        "exchange": "NASDAQ",
        "company_name": "Tesla Inc.", 
        "price": "245.67",
        "change": "+11.45",
        "change_percent": "+4.89%",
        "currency": "USD",
        "prev_close": "234.22",
        "after_hours": "247.80",
        "key_stats": {
            "Market Cap": "780.5B",
            "P/E Ratio": "68.2",
            "52W High": "299.29",
            "52W Low": "152.37",
            "Volume": "118.7M",
            "Avg Volume": "125.3M",
            "Dividend": "0.00",
            "Yield": "0.00%"
        },
        "about": "Tesla, Inc. designs, develops, manufactures, and sells fully electric vehicles and energy generation and storage systems, and also offers services related to its products.",
        "news": [
            {"headline": "Tesla Delivers Record Quarterly Numbers", "source": "CNBC", "url": "https://cnbc.com/tesla-earnings"},
            {"headline": "Tesla Announces New Gigafactory Location", "source": "Reuters", "url": "https://reuters.com/tesla-gigafactory"},
            {"headline": "Tesla FSD Beta Shows Major Improvements", "source": "The Verge", "url": "https://theverge.com/tesla-fsd"}
        ]
    },
    "GOOGL": {
        "ticker": "GOOGL",
        "exchange": "NASDAQ",
        "company_name": "Alphabet Inc.",
        "price": "142.67", 
        "change": "+2.61",
        "change_percent": "+1.87%",
        "currency": "USD",
        "prev_close": "140.06",
        "after_hours": "143.10",
        "key_stats": {
            "Market Cap": "1.78T",
            "P/E Ratio": "25.6",
            "52W High": "152.10",
            "52W Low": "118.23",
            "Volume": "28.9M",
            "Avg Volume": "32.1M",
            "Dividend": "0.00",
            "Yield": "0.00%"
        },
        "about": "Alphabet Inc. provides various products and platforms in the United States, Europe, the Middle East, Africa, and the Americas. It operates through Google Services, Google Cloud, and Other Bets segments.",
        "news": [
            {"headline": "Google AI Advances Show Promise in Healthcare", "source": "MIT Technology Review", "url": "https://technologyreview.com/google-ai"},
            {"headline": "Alphabet Cloud Revenue Beats Expectations", "source": "Financial Times", "url": "https://ft.com/alphabet-cloud"},
            {"headline": "Google Search Gets Major AI Overhaul", "source": "The Verge", "url": "https://theverge.com/google-search"}
        ]
    }
}

def get_mock_market_data(section: str) -> Dict[str, Any]:
    """Get mock market data for a section"""
    return MOCK_MARKET_DATA.get(section, {
        "section": section,
        "title": f"{section.title()}",
        "count": 0,
        "items": [],
        "error": f"Section '{section}' not found in mock data"
    })

def get_mock_quote(ticker: str) -> Dict[str, Any]:
    """Get mock quote data for a ticker"""
    ticker = ticker.upper()
    if ticker in MOCK_QUOTES:
        return MOCK_QUOTES[ticker]
    
    # Return a generic mock quote for unknown tickers
    import random
    base_price = random.uniform(50, 500)
    change = random.uniform(-10, 10)
    change_percent = (change / base_price) * 100
    
    return {
        "ticker": ticker,
        "exchange": "NASDAQ",
        "company_name": f"{ticker} Corporation",
        "price": f"{base_price:.2f}",
        "change": f"{change:+.2f}",
        "change_percent": f"{change_percent:+.2f}%",
        "currency": "USD",
        "prev_close": f"{base_price - change:.2f}",
        "after_hours": f"{base_price + random.uniform(-2, 2):.2f}",
        "key_stats": {
            "Market Cap": f"{random.uniform(1, 1000):.1f}B",
            "P/E Ratio": f"{random.uniform(10, 50):.1f}",
            "52W High": f"{base_price * 1.3:.2f}",
            "52W Low": f"{base_price * 0.7:.2f}",
            "Volume": f"{random.uniform(10, 100):.1f}M",
            "Avg Volume": f"{random.uniform(10, 100):.1f}M",
            "Dividend": f"{random.uniform(0, 2):.2f}",
            "Yield": f"{random.uniform(0, 3):.1f}%"
        },
        "about": f"{ticker} Corporation is a leading company in its sector, providing innovative products and services to customers worldwide.",
        "news": [
            {"headline": f"{ticker} Reports Strong Quarterly Results", "source": "Financial News", "url": "#"},
            {"headline": f"{ticker} Announces New Product Launch", "source": "Tech News", "url": "#"},
            {"headline": f"Analysts Upgrade {ticker} Stock Rating", "source": "Market Watch", "url": "#"}
        ]
    }

def get_mock_overview() -> Dict[str, Any]:
    """Get mock market overview"""
    return {
        "timestamp": datetime.now().isoformat(),
        "sections": MOCK_MARKET_DATA,
        "market_status": "open" if 9 <= datetime.now().hour <= 16 else "closed",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
