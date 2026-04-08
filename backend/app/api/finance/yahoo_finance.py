"""
scrapers/yahoo_finance.py  —  Yahoo Finance with Auth Session
=============================================================
Uses auth/auth_session.py for all requests.
v10 (quote, financials, holders) → needs crumb → auto-managed
v8/v7/v1 (chart, options, search, movers) → free, no crumb
"""
import json
from typing import Any, Optional
from auth.auth_session import yahoo_fetch_free, yahoo_fetch_auth
from utils.cache import get as c_get, set as c_set

Q1 = "https://query1.finance.yahoo.com"
Q2 = "https://query2.finance.yahoo.com"

SUMMARY_MODULES   = "price,summaryDetail,financialData,defaultKeyStatistics,quoteType,summaryProfile,calendarEvents,earnings,earningsTrend,recommendationTrend,upgradeDowngradeHistory"
FINANCIAL_MODULES = "incomeStatementHistory,incomeStatementHistoryQuarterly,balanceSheetHistory,balanceSheetHistoryQuarterly,cashflowStatementHistory,cashflowStatementHistoryQuarterly,earnings,earningsHistory"
HOLDERS_MODULES   = "institutionOwnership,insiderHolders,majorHoldersBreakdown,insiderTransactions,netSharePurchaseActivity"


def _rv(obj: Any, key: str) -> Any:
    if not isinstance(obj, dict): return obj
    v = obj.get(key, {})
    if isinstance(v, dict): return v.get("fmt") or v.get("raw")
    return v


async def _quote_from_chart(ticker: str) -> dict:
    """v8 fallback — always works, no crumb."""
    try:
        r = await yahoo_fetch_free(f"{Q1}/v8/finance/chart/{ticker}",
            {"interval":"1d","range":"1d","includePrePost":"true"}, ticker=ticker)
        if r.status_code == 200:
            meta = r.json()["chart"]["result"][0]["meta"]
            return {
                "ticker": ticker, "name": meta.get("longName") or meta.get("shortName"),
                "exchange": meta.get("exchangeName"), "currency": meta.get("currency"),
                "price": meta.get("regularMarketPrice"), "prev_close": meta.get("chartPreviousClose"),
                "52w_high": meta.get("fiftyTwoWeekHigh"), "52w_low": meta.get("fiftyTwoWeekLow"),
                "volume": meta.get("regularMarketVolume"),
                "_source": "v8_chart_fallback",
                "_note": "v10 crumb auth failed — using v8 chart for price data. "
                         "Set Yahoo cookies via POST /auth/yahoo/cookies for full 60+ field quote.",
            }
    except Exception:
        pass
    return {"error": "No data available", "ticker": ticker}


def _flatten(data: dict, ticker: str) -> dict:
    if "_error" in data:
        return {"error": data["_error"], "ticker": ticker,
                "_auth_failed": True, "note": data.get("_note","")}
    qs_wrap = data.get("quoteSummary", {})
    if qs_wrap.get("error"):
        return {"error": str(qs_wrap["error"]), "ticker": ticker}
    result_list = qs_wrap.get("result") or []
    if not result_list:
        return {"error": "Empty result", "ticker": ticker}

    qs = result_list[0]
    price   = qs.get("price",               {})
    detail  = qs.get("summaryDetail",        {})
    fin     = qs.get("financialData",        {})
    stats   = qs.get("defaultKeyStatistics", {})
    profile = qs.get("summaryProfile",       {})
    qtype   = qs.get("quoteType",            {})
    cal     = qs.get("calendarEvents",       {})
    rec     = qs.get("recommendationTrend",  {})
    earn    = qs.get("earnings",             {})
    upg     = qs.get("upgradeDowngradeHistory", {})

    rec_trend = None
    if rec.get("trend"):
        lt = rec["trend"][0]
        rec_trend = {k: lt.get(k) for k in ("period","strongBuy","buy","hold","sell","strongSell")}

    earn_q = [{"period": q.get("date"), "actual": _rv(q,"actual"), "estimate": _rv(q,"estimate")}
              for q in (earn.get("earningsChart",{}).get("quarterly") or [])]

    earn_dates = [d.get("fmt") or d.get("raw") for d in
                  (cal.get("earnings",{}).get("earningsDate") or []) if d.get("fmt") or d.get("raw")]

    upg_list = [{k: u.get(k) for k in ("firm","fromGrade","toGrade","action","epochGradeDate")}
                for u in (upg.get("history") or [])[:5]]

    return {
        "ticker": ticker.upper(), "name": price.get("shortName") or price.get("longName"),
        "long_name": price.get("longName"), "exchange": price.get("exchangeName"),
        "exchange_full": qtype.get("fullExchangeName"), "quote_type": price.get("quoteType"),
        "currency": price.get("currency"), "timezone": qtype.get("exchangeTimezoneName"),
        "price":            _rv(price,"regularMarketPrice"),
        "open":             _rv(price,"regularMarketOpen"),
        "high":             _rv(price,"regularMarketDayHigh"),
        "low":              _rv(price,"regularMarketDayLow"),
        "prev_close":       _rv(price,"regularMarketPreviousClose"),
        "volume":           _rv(price,"regularMarketVolume"),
        "avg_volume":       _rv(detail,"averageVolume"),
        "avg_volume_10d":   _rv(detail,"averageVolume10days"),
        "change":           _rv(price,"regularMarketChange"),
        "change_percent":   _rv(price,"regularMarketChangePercent"),
        "pre_market_price": _rv(price,"preMarketPrice"),
        "pre_market_change":_rv(price,"preMarketChange"),
        "pre_market_change_pct": _rv(price,"preMarketChangePercent"),
        "post_market_price":_rv(price,"postMarketPrice"),
        "post_market_change":_rv(price,"postMarketChange"),
        "post_market_change_pct": _rv(price,"postMarketChangePercent"),
        "market_state":     price.get("marketState"),
        "market_cap":       _rv(price,"marketCap"),
        "enterprise_value": _rv(stats,"enterpriseValue"),
        "pe_ratio":         _rv(detail,"trailingPE"),
        "forward_pe":       _rv(detail,"forwardPE"),
        "peg_ratio":        _rv(stats,"pegRatio"),
        "price_to_book":    _rv(stats,"priceToBook"),
        "price_to_sales":   _rv(stats,"priceToSalesTrailing12Months"),
        "enterprise_to_revenue": _rv(stats,"enterpriseToRevenue"),
        "enterprise_to_ebitda":  _rv(stats,"enterpriseToEbitda"),
        "52w_high": _rv(detail,"fiftyTwoWeekHigh"), "52w_low": _rv(detail,"fiftyTwoWeekLow"),
        "52w_change": _rv(stats,"52WeekChange"), "50d_avg": _rv(detail,"fiftyDayAverage"),
        "200d_avg": _rv(detail,"twoHundredDayAverage"),
        "eps": _rv(stats,"trailingEps"), "forward_eps": _rv(stats,"forwardEps"),
        "revenue": _rv(fin,"totalRevenue"), "revenue_per_share": _rv(fin,"revenuePerShare"),
        "ebitda": _rv(fin,"ebitda"), "earnings_growth": _rv(fin,"earningsGrowth"),
        "revenue_growth": _rv(fin,"revenueGrowth"), "profit_margins": _rv(fin,"profitMargins"),
        "gross_margins": _rv(fin,"grossMargins"), "operating_margins": _rv(fin,"operatingMargins"),
        "return_on_assets": _rv(fin,"returnOnAssets"), "return_on_equity": _rv(fin,"returnOnEquity"),
        "total_cash": _rv(fin,"totalCash"), "total_cash_per_share": _rv(fin,"totalCashPerShare"),
        "total_debt": _rv(fin,"totalDebt"), "debt_to_equity": _rv(fin,"debtToEquity"),
        "current_ratio": _rv(fin,"currentRatio"), "book_value": _rv(stats,"bookValue"),
        "shares_outstanding": _rv(stats,"sharesOutstanding"), "shares_float": _rv(stats,"floatShares"),
        "shares_short": _rv(stats,"sharesShort"), "short_ratio": _rv(stats,"shortRatio"),
        "short_pct_float": _rv(stats,"shortPercentOfFloat"),
        "dividend_rate": _rv(detail,"dividendRate"), "dividend_yield": _rv(detail,"dividendYield"),
        "ex_dividend_date": _rv(detail,"exDividendDate"), "payout_ratio": _rv(detail,"payoutRatio"),
        "5yr_avg_div_yield": _rv(detail,"fiveYearAvgDividendYield"),
        "beta": _rv(detail,"beta"),
        "target_high": _rv(fin,"targetHighPrice"), "target_low": _rv(fin,"targetLowPrice"),
        "target_mean": _rv(fin,"targetMeanPrice"), "target_median": _rv(fin,"targetMedianPrice"),
        "recommendation": fin.get("recommendationKey"),
        "analyst_count": (fin.get("numberOfAnalystOpinions") or {}).get("raw"),
        "analyst_trend": rec_trend, "recent_upgrades": upg_list,
        "earnings_dates": earn_dates, "quarterly_earnings": earn_q,
        "sector": profile.get("sector"), "industry": profile.get("industry"),
        "employees": profile.get("fullTimeEmployees"), "website": profile.get("website"),
        "headquarters": {"city": profile.get("city"), "state": profile.get("state"),
                         "country": profile.get("country")},
        "description": profile.get("longBusinessSummary"),
    }


async def get_quote(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    if c := c_get("yf_q", {"t": ticker}): return c
    try:
        r    = await yahoo_fetch_auth(f"/v10/finance/quoteSummary/{ticker}",
                   {"modules": SUMMARY_MODULES, "lang": "en", "region": "US"}, ticker=ticker)
        flat = _flatten(r.json() if r.status_code == 200 else {}, ticker)
    except Exception as ex:
        flat = {"_auth_failed": True, "error": str(ex), "ticker": ticker}
    if flat.get("_auth_failed"):
        flat = await _quote_from_chart(ticker)
    if "error" not in flat:
        c_set("yf_q", {"t": ticker}, flat, ttl=60)
    return flat


async def get_chart(ticker: str, interval: str = "1d", range_: str = "1mo") -> dict:
    ticker = ticker.upper().strip()
    ck = {"t": ticker, "i": interval, "r": range_}
    if c := c_get("yf_ch", ck): return c
    try:
        r     = await yahoo_fetch_free(f"{Q1}/v8/finance/chart/{ticker}",
                    {"interval":interval,"range":range_,"lang":"en","region":"US",
                     "includePrePost":"true","events":"div,splits"}, ticker=ticker)
        chart = r.json()["chart"]["result"][0]
        meta  = chart.get("meta",{}); ts = chart.get("timestamp",[])
        q     = chart.get("indicators",{}).get("quote",[{}])[0]
        adj   = chart.get("indicators",{}).get("adjclose",[{}])
        adjc  = adj[0].get("adjclose") if adj else None
        events= chart.get("events",{})
        result = {
            "ticker": ticker, "interval": interval, "range": range_,
            "exchange": meta.get("exchangeName"), "currency": meta.get("currency"),
            "instrument": meta.get("instrumentType"), "timezone": meta.get("timezone"),
            "current_price": meta.get("regularMarketPrice"), "candle_count": len(ts),
            "candles": [{"timestamp":ts[i],"open":q.get("open",[None])[i],
                         "high":q.get("high",[None])[i],"low":q.get("low",[None])[i],
                         "close":q.get("close",[None])[i],"volume":q.get("volume",[None])[i],
                         "adj_close":adjc[i] if adjc else None} for i in range(len(ts))],
            "dividends":[{"date":v.get("date"),"amount":v.get("amount")} for v in events.get("dividends",{}).values()],
            "splits":[{"date":v.get("date"),"ratio":f'{v.get("numerator")}/{v.get("denominator")}'}
                      for v in events.get("splits",{}).values()],
        }
        c_set("yf_ch", ck, result, ttl=300)
        return result
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}


async def get_financials(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    if c := c_get("yf_fin", {"t": ticker}): return c
    try:
        r  = await yahoo_fetch_auth(f"/v10/finance/quoteSummary/{ticker}",
                 {"modules": FINANCIAL_MODULES, "lang": "en", "region": "US"}, ticker=ticker)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "ticker": ticker,
                    "hint": "Set Yahoo cookies via POST /auth/yahoo/cookies for financials access"}
        qs = r.json()["quoteSummary"]["result"][0]
        result = {
            "ticker": ticker,
            "annual": {
                "income_statement": qs.get("incomeStatementHistory",{}).get("incomeStatementHistory",[]),
                "balance_sheet":    qs.get("balanceSheetHistory",{}).get("balanceSheetStatements",[]),
                "cash_flow":        qs.get("cashflowStatementHistory",{}).get("cashflowStatements",[]),
            },
            "quarterly": {
                "income_statement": qs.get("incomeStatementHistoryQuarterly",{}).get("incomeStatementHistory",[]),
                "balance_sheet":    qs.get("balanceSheetHistoryQuarterly",{}).get("balanceSheetStatements",[]),
                "cash_flow":        qs.get("cashflowStatementHistoryQuarterly",{}).get("cashflowStatements",[]),
            },
            "earnings": qs.get("earnings",{}),
            "earnings_history": qs.get("earningsHistory",{}).get("history",[]),
        }
        c_set("yf_fin", {"t": ticker}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}


async def get_holders(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    if c := c_get("yf_hld", {"t": ticker}): return c
    try:
        r  = await yahoo_fetch_auth(f"/v10/finance/quoteSummary/{ticker}",
                 {"modules": HOLDERS_MODULES, "lang": "en", "region": "US"}, ticker=ticker)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "ticker": ticker}
        qs = r.json()["quoteSummary"]["result"][0]
        result = {
            "ticker": ticker,
            "major":        qs.get("majorHoldersBreakdown",{}),
            "institutions": qs.get("institutionOwnership",{}).get("ownershipList",[]),
            "insiders":     qs.get("insiderHolders",{}).get("holders",[]),
            "transactions": qs.get("insiderTransactions",{}).get("transactions",[]),
            "net_purchase": qs.get("netSharePurchaseActivity",{}),
        }
        c_set("yf_hld", {"t": ticker}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}


async def get_options(ticker: str, expiry_date: Optional[str] = None) -> dict:
    ticker = ticker.upper().strip()
    params: dict = {"lang":"en","region":"US"}
    if expiry_date: params["date"] = expiry_date
    try:
        r     = await yahoo_fetch_free(f"{Q1}/v7/finance/options/{ticker}", params, ticker=ticker)
        chain = r.json()["optionChain"]["result"][0]
        opts  = chain.get("options",[{}])[0]
        return {"ticker": ticker, "expiration_dates": chain.get("expirationDates",[]),
                "strikes": chain.get("strikes",[]), "calls": opts.get("calls",[]),
                "puts": opts.get("puts",[])}
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}


async def search(query: str) -> dict:
    if c := c_get("yf_s", {"q": query}): return c
    try:
        r = await yahoo_fetch_free(f"{Q1}/v1/finance/search",
              {"q":query,"lang":"en","region":"US","quotesCount":10,"newsCount":8,"enableFuzzyQuery":"true"})
        data = r.json()
        result = {"query": query, "quotes": data.get("quotes",[]),
                  "news": data.get("news",[]), "lists": data.get("lists",[])}
        c_set("yf_s", {"q": query}, result, ttl=300)
        return result
    except Exception as ex:
        return {"error": str(ex), "query": query}


async def get_trending(region: str = "US") -> dict:
    try:
        r  = await yahoo_fetch_free(f"{Q1}/v1/finance/trending/{region.upper()}", {})
        qs = r.json()["finance"]["result"][0].get("quotes",[])
        return {"region": region.upper(), "tickers": [q["symbol"] for q in qs if q.get("symbol")]}
    except Exception as ex:
        return {"region": region, "tickers": [], "error": str(ex)}


async def get_movers(mover_type: str = "day_gainers", count: int = 25) -> dict:
    VALID = {"day_gainers","day_losers","most_actives","small_cap_gainers",
             "growth_technology_stocks","undervalued_growth_stocks","undervalued_large_caps"}
    if mover_type not in VALID:
        return {"error": f"Invalid type. Choose: {sorted(VALID)}"}
    try:
        r   = await yahoo_fetch_free(f"{Q1}/v1/finance/screener/predefined/saved",
                  {"scrIds":mover_type,"count":count,"lang":"en","region":"US"})
        res = r.json()["finance"]["result"][0]
        return {"type":mover_type,"total":res.get("total",0),
                "count":len(res.get("quotes",[])),"movers":res.get("quotes",[])}
    except Exception as ex:
        return {"error": str(ex), "type": mover_type}


async def get_recommendations(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    try:
        r    = await yahoo_fetch_free(f"{Q1}/v6/finance/recommendationsbysymbol/{ticker}", {}, ticker=ticker)
        recs = r.json()["finance"]["result"][0].get("recommendedSymbols",[])
        if recs: return {"ticker": ticker, "recommend": recs}
    except Exception:
        pass
    s = await search(ticker)
    return {"ticker": ticker, "recommend": s.get("quotes",[])[:8], "_source": "search_fallback"}


async def get_spark(tickers: list[str], range_: str = "1d", interval: str = "1d") -> dict:
    import asyncio
    async def _one(t):
        try:
            r  = await yahoo_fetch_free(f"{Q1}/v8/finance/chart/{t.upper()}",
                     {"interval":interval,"range":range_}, ticker=t)
            d  = r.json()["chart"]["result"][0]
            m  = d["meta"]
            ts = d.get("timestamp",[])
            cl = d.get("indicators",{}).get("quote",[{}])[0].get("close",[])
            return {"symbol":t.upper(),"currency":m.get("currency"),
                    "current_price":m.get("regularMarketPrice"),
                    "prev_close":m.get("chartPreviousClose"),"timestamps":ts,"closes":cl}
        except Exception:
            return {"symbol": t.upper(), "error": "no data"}
    results = await asyncio.gather(*[_one(t) for t in tickers[:20]], return_exceptions=True)
    return {"tickers":tickers,"range":range_,"interval":interval,
            "sparklines":[r if not isinstance(r,Exception) else {} for r in results]}
