"""routers/yahoo_finance.py"""
from fastapi import APIRouter, Query, Path
from scrapers import yahoo_finance as yf
from typing import Optional, List

router = APIRouter()

@router.get(
    "/quote/{ticker}",
    summary="Full stock quote — 60+ fields",
    description="""
Complete Yahoo Finance quote summary.

**Returns 60+ fields including:**
- Live price, OHLC, volume, market state (pre/post market included)
- Market cap, P/E, forward P/E, PEG, Price/Book, Price/Sales
- 52-week high/low, 50-day/200-day moving averages
- EPS, revenue, profit margins, ROE, ROA, debt/equity
- Dividend yield, ex-dividend date, payout ratio
- Analyst target prices, recommendation (buy/hold/sell)
- Sector, industry, headquarters, description, website
- Upcoming earnings dates, quarterly earnings history
- Recent analyst upgrades/downgrades
""",
)
async def quote(ticker: str = Path(..., description="e.g. AAPL, TSLA, RELIANCE.NS")):
    return await yf.get_quote(ticker)


@router.get(
    "/chart/{ticker}",
    summary="OHLCV candlestick data",
    description="""
Historical price candlestick data with splits and dividends.

**interval:** `1m` | `2m` | `5m` | `15m` | `30m` | `60m` | `1h` | `1d` | `1wk` | `1mo`

**range:** `1d` | `5d` | `1mo` | `3mo` | `6mo` | `1y` | `2y` | `5y` | `10y` | `ytd` | `max`

Note: 1m data only available for last 7 days. Short intervals require short ranges.
""",
)
async def chart(
    ticker:   str = Path(...),
    interval: str = Query("1d",  description="Candle size: 1m|5m|15m|30m|60m|1d|1wk|1mo"),
    range:    str = Query("1mo", description="Time range: 1d|5d|1mo|3mo|6mo|1y|2y|5y|max"),
):
    return await yf.get_chart(ticker, interval, range)


@router.get(
    "/financials/{ticker}",
    summary="Income statement, balance sheet, cash flow",
    description="Annual and quarterly financial statements — income statement, balance sheet, cash flow.",
)
async def financials(ticker: str = Path(...)):
    return await yf.get_financials(ticker)


@router.get(
    "/holders/{ticker}",
    summary="Institutional + insider holders",
    description="Major holders breakdown, institutional ownership list, insider transactions.",
)
async def holders(ticker: str = Path(...)):
    return await yf.get_holders(ticker)


@router.get(
    "/options/{ticker}",
    summary="Options chain (calls + puts)",
    description="Full options chain with all expiry dates, strikes, calls, and puts.",
)
async def options(
    ticker:      str = Path(...),
    expiry_date: Optional[str] = Query(None, description="Unix timestamp for specific expiry"),
):
    return await yf.get_options(ticker, expiry_date)


@router.get(
    "/search",
    summary="Search tickers and news",
    description="Search Yahoo Finance for tickers, companies, ETFs, and related news.",
)
async def search(q: str = Query(..., description="Search query")):
    return await yf.search(q)


@router.get(
    "/trending",
    summary="Trending tickers",
)
async def trending(region: str = Query("US", description="Region code: US | IN | GB | AU | CA")):
    return await yf.get_trending(region)


@router.get(
    "/movers",
    summary="Market movers — gainers, losers, most active",
    description="""
Market movers from Yahoo Finance screener.

**type options:**
- `day_gainers` — top gaining stocks today
- `day_losers` — top losing stocks today
- `most_actives` — highest volume stocks
- `small_cap_gainers`
- `growth_technology_stocks`
- `undervalued_growth_stocks`
- `undervalued_large_caps`
""",
)
async def movers(
    type:  str = Query("day_gainers", description="day_gainers|day_losers|most_actives|..."),
    count: int = Query(25, description="Number of results (max 50)"),
):
    return await yf.get_movers(type, min(count, 50))


@router.get(
    "/recommendations/{ticker}",
    summary="Related / recommended tickers",
)
async def recommendations(ticker: str = Path(...)):
    return await yf.get_recommendations(ticker)


@router.get(
    "/sparkline",
    summary="Mini price chart for multiple tickers",
    description="Lightweight sparkline data for up to 20 tickers at once.",
)
async def sparkline(
    tickers:  str = Query(..., description="Comma-separated tickers: AAPL,MSFT,GOOGL"),
    range:    str = Query("1d", description="1d|5d|1mo|3mo|6mo|1y"),
    interval: str = Query("1d", description="1m|5m|1d|1wk"),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()][:20]
    return await yf.get_spark(ticker_list, range, interval)


@router.get(
    "/site-map",
    summary="All Yahoo Finance internal API endpoints",
)
async def site_map():
    return {
        "hosts": {
            "primary":   "query1.finance.yahoo.com",
            "alternate": "query2.finance.yahoo.com",
        },
        "port":     443,
        "protocol": "HTTPS / TLS",
        "method":   "GET",
        "auth":     "None — public endpoints",
        "endpoints": [
            {
                "path":    "/v8/finance/chart/{ticker}",
                "params":  ["interval", "range", "includePrePost", "events"],
                "returns": "OHLCV candles + splits + dividends",
            },
            {
                "path":    "/v10/finance/quoteSummary/{ticker}",
                "params":  ["modules (comma-separated list)"],
                "modules": [
                    "price", "summaryDetail", "financialData",
                    "defaultKeyStatistics", "quoteType", "summaryProfile",
                    "calendarEvents", "earnings", "earningsTrend",
                    "recommendationTrend", "upgradeDowngradeHistory",
                    "incomeStatementHistory", "balanceSheetHistory",
                    "cashflowStatementHistory", "institutionOwnership",
                    "insiderHolders", "majorHoldersBreakdown",
                ],
                "returns": "Any combination of 20+ data modules",
            },
            {
                "path":    "/v7/finance/options/{ticker}",
                "params":  ["date (unix timestamp)"],
                "returns": "Options chain — expiry dates, strikes, calls, puts",
            },
            {
                "path":    "/v1/finance/search",
                "params":  ["q", "quotesCount", "newsCount", "enableFuzzyQuery"],
                "returns": "Quotes + news + lists + research",
            },
            {
                "path":    "/v1/finance/trending/{region}",
                "returns": "Trending tickers",
            },
            {
                "path":    "/v1/finance/screener/predefined/saved",
                "params":  ["scrIds", "count"],
                "returns": "Screener results (gainers/losers/actives)",
            },
            {
                "path":    "/v6/finance/recommendationsbysymbol/{ticker}",
                "returns": "Related tickers",
            },
            {
                "path":    "/v7/finance/spark",
                "params":  ["symbols", "range", "interval"],
                "returns": "Sparkline data for multiple tickers",
            },
        ],
        "required_headers": {
            "Referer": "https://finance.yahoo.com/",
            "Accept":  "application/json",
        },
        "fallback": "Automatically retries on query2.finance.yahoo.com if query1 fails",
    }
