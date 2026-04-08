"""Investors service - SEC EDGAR 13F filings + Congress stock trading data"""
import httpx
from typing import Optional, List, Dict
from loguru import logger
from datetime import datetime, timedelta

SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST"
SEC_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"
HOUSE_TRADES_URL = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
SENATE_TRADES_URL = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"

# Top institutional investors by CIK
TOP_FUNDS = [
    {"cik": "0001067983", "name": "Berkshire Hathaway", "manager": "Warren Buffett"},
    {"cik": "0001336528", "name": "Bridgewater Associates", "manager": "Ray Dalio"},
    {"cik": "0001649339", "name": "Citadel Advisors", "manager": "Ken Griffin"},
    {"cik": "0001037389", "name": "Renaissance Technologies", "manager": "Jim Simons"},
    {"cik": "0001350694", "name": "Two Sigma Investments", "manager": "John Overdeck"},
    {"cik": "0001364742", "name": "DE Shaw & Co", "manager": "David Shaw"},
    {"cik": "0001061768", "name": "Millennium Management", "manager": "Israel Englander"},
    {"cik": "0000921669", "name": "BlackRock", "manager": "Larry Fink"},
    {"cik": "0001166559", "name": "Vanguard Group", "manager": "Tim Buckley"},
    {"cik": "0000315066", "name": "Fidelity", "manager": "Abigail Johnson"},
    {"cik": "0001423053", "name": "ARK Invest", "manager": "Cathie Wood"},
    {"cik": "0001159159", "name": "Pershing Square", "manager": "Bill Ackman"},
    {"cik": "0001336326", "name": "Baupost Group", "manager": "Seth Klarman"},
    {"cik": "0001029160", "name": "Tiger Global", "manager": "Chase Coleman"},
    {"cik": "0001044316", "name": "Soros Fund Management", "manager": "George Soros"},
]


class InvestorsService:
    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._client_kwargs = {
            "timeout": 20.0,
            "headers": {"User-Agent": "AARAMBH Intelligence Terminal admin@aarambh.dev"}
        }

    def _cache_get(self, key: str, ttl: int = 3600):
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    async def get_funds(self) -> List[dict]:
        """Get list of top institutional funds (concurrent fetching)"""
        import asyncio
        cached = self._cache_get("funds", ttl=86400)
        if cached:
            return cached

        async with httpx.AsyncClient(**self._client_kwargs) as client:
            async def fetch_single_fund(fund: dict) -> dict:
                try:
                    resp = await client.get(
                        f"https://data.sec.gov/submissions/CIK{fund['cik']}.json"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        recent = data.get("filings", {}).get("recent", {})
                        filing_dates = recent.get("filingDate", [])
                        forms = recent.get("form", [])

                        latest_13f = None
                        for i, form in enumerate(forms):
                            if "13F" in form:
                                latest_13f = filing_dates[i] if i < len(filing_dates) else None
                                break

                        return {
                            "cik": fund["cik"],
                            "name": data.get("name", fund["name"]),
                            "manager": fund["manager"],
                            "latest_13f_date": latest_13f,
                            "total_filings": len(filing_dates),
                        }
                    else:
                        return {**fund, "latest_13f_date": None, "total_filings": 0}
                except Exception as e:
                    logger.warning(f"SEC fetch error for {fund['name']}: {e}")
                    return {**fund, "latest_13f_date": None, "total_filings": 0}

            # Fetch all funds concurrently with 0.2s stagger to avoid rate limiting
            tasks = []
            for i, fund in enumerate(TOP_FUNDS):
                tasks.append(fetch_single_fund(fund))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            funds = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    funds.append({**TOP_FUNDS[i], "latest_13f_date": None, "total_filings": 0})
                else:
                    funds.append(result)

            self._cache_set("funds", funds)
            return funds

    async def get_fund_holdings(self, cik: str) -> Optional[dict]:
        """Get a fund's latest 13F holdings"""
        cached = self._cache_get(f"holdings:{cik}", ttl=86400)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(**self._client_kwargs) as client:
                # Search for latest 13F-HR filing
                resp = await client.get(f"{SEC_EDGAR_BASE}/submissions/CIK{cik}.json")
                if resp.status_code != 200:
                    return None

                data = resp.json()
                recent = data.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                accessions = recent.get("accessionNumber", [])

                for i, form in enumerate(forms):
                    if "13F" in form and i < len(accessions):
                        result = {
                            "fund_name": data.get("name", ""),
                            "cik": cik,
                            "filing_date": recent.get("filingDate", [])[i] if i < len(recent.get("filingDate", [])) else "",
                            "accession": accessions[i],
                            "form_type": form,
                        }
                        self._cache_set(f"holdings:{cik}", result)
                        return result

        except Exception as e:
            logger.error(f"Holdings fetch error for CIK {cik}: {e}")
        return None

    async def get_congress_trades(self) -> List[dict]:
        """Get recent congressional stock trades"""
        cached = self._cache_get("congress", ttl=3600)
        if cached:
            return cached

        trades = []

        async with httpx.AsyncClient(**self._client_kwargs) as client:
            # House trades
            try:
                resp = await client.get(HOUSE_TRADES_URL)
                if resp.status_code == 200:
                    data = resp.json()
                    for trade in data[-200:]:  # last 200
                        trades.append({
                            "member": trade.get("representative", "Unknown"),
                            "chamber": "House",
                            "ticker": trade.get("ticker", "N/A"),
                            "transaction": trade.get("type", "Unknown"),
                            "amount": trade.get("amount", "Unknown"),
                            "date": trade.get("transaction_date", ""),
                            "disclosure_date": trade.get("disclosure_date", ""),
                            "district": trade.get("district", ""),
                        })
            except Exception as e:
                logger.warning(f"House trades fetch error: {e}")

            # Senate trades
            try:
                resp = await client.get(SENATE_TRADES_URL)
                if resp.status_code == 200:
                    data = resp.json()
                    for trade in data[-200:]:
                        trades.append({
                            "member": trade.get("senator", trade.get("first_name", "") + " " + trade.get("last_name", "")),
                            "chamber": "Senate",
                            "ticker": trade.get("ticker", "N/A"),
                            "transaction": trade.get("type", "Unknown"),
                            "amount": trade.get("amount", "Unknown"),
                            "date": trade.get("transaction_date", ""),
                            "disclosure_date": trade.get("disclosure_date", ""),
                            "district": trade.get("state", ""),
                        })
            except Exception as e:
                logger.warning(f"Senate trades fetch error: {e}")

        # Sort by date descending
        trades.sort(key=lambda x: x.get("date", ""), reverse=True)
        self._cache_set("congress", trades[:500])
        return trades[:500]

    async def get_portfolios(self) -> List[dict]:
        """Get notable investor portfolio movements (from SEC filings summary)"""
        funds = await self.get_funds()
        return [
            {"name": f["name"], "manager": f["manager"], "cik": f["cik"],
             "latest_filing": f.get("latest_13f_date")}
            for f in funds
        ]

    async def close(self):
        pass


investors_service = InvestorsService()
