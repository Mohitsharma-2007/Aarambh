"""COT (Commitments of Traders) Data Service - Fixed parser for real CFTC data"""
import httpx
import io
import zipfile
import csv
from typing import List
from loguru import logger
from datetime import datetime


class CotService:
    """Service for fetching COT data from CFTC"""

    _cache = {}
    _cache_ts = {}

    def _get_url(self):
        year = datetime.now().year
        return f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"

    async def get_financial_futures_data(self) -> List[dict]:
        """Fetch and parse COT data for financial futures"""
        # Check cache (COT updates weekly, cache for 6 hours)
        cached = self._cache.get("cot_data")
        cached_ts = self._cache_ts.get("cot_data", 0)
        if cached and (datetime.now().timestamp() - cached_ts) < 21600:
            return cached

        try:
            url = self._get_url()
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                logger.info(f"Downloading COT data from {url}")
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                    if not txt_files:
                        logger.error("No text files found in COT zip")
                        return self._get_fallback_data()

                    with z.open(txt_files[0]) as f:
                        content = f.read().decode('latin-1')

                        # COT financial futures format is comma-delimited
                        reader = csv.DictReader(io.StringIO(content))
                        rows = list(reader)

                        if not rows:
                            return self._get_fallback_data()

                        # Target markets
                        targets = {
                            'E-MINI S&P 500': 'S&P 500',
                            'S&P 500': 'S&P 500',
                            'NASDAQ-100': 'NASDAQ-100',
                            'NASDAQ MINI': 'NASDAQ-100',
                            'E-MINI NASDAQ': 'NASDAQ-100',
                            'RUSSELL 2000': 'Russell 2000',
                            'E-MINI RUSSELL': 'Russell 2000',
                            'BITCOIN': 'Bitcoin',
                            'GOLD': 'Gold',
                            'SILVER': 'Silver',
                            'CRUDE OIL': 'Crude Oil',
                            'NATURAL GAS': 'Natural Gas',
                            'EURO FX': 'EUR/USD',
                            '10-YEAR': '10Y T-Note',
                            '10 YEAR': '10Y T-Note',
                            '2-YEAR': '2Y T-Note',
                            '5-YEAR': '5Y T-Note',
                            '30-YEAR': '30Y T-Bond',
                        }

                        # Get latest report date
                        dates = set()
                        date_col = None
                        for col in rows[0].keys():
                            if 'date' in col.lower() and 'report' in col.lower():
                                date_col = col
                                break
                            if 'As_of_Date' in col or 'Report_Date' in col:
                                date_col = col
                                break

                        if date_col:
                            for row in rows:
                                dates.add(row.get(date_col, ''))
                            latest_date = max(dates) if dates else None
                        else:
                            latest_date = None

                        data = []
                        seen = set()

                        for row in rows:
                            # Only latest report
                            if latest_date and date_col and row.get(date_col) != latest_date:
                                continue

                            # Find market name column
                            market_name = ''
                            for col in row.keys():
                                if 'market' in col.lower() or 'name' in col.lower():
                                    market_name = row[col].strip()
                                    break
                            if not market_name:
                                market_name = list(row.values())[0].strip() if row else ''

                            # Match to target
                            matched_name = None
                            for key, display in targets.items():
                                if key.upper() in market_name.upper():
                                    matched_name = display
                                    break

                            if matched_name and matched_name not in seen:
                                seen.add(matched_name)

                                # Extract position columns
                                def get_val(row, keywords):
                                    for col in row.keys():
                                        col_normalized = col.lower().replace('_', ' ').replace('-', ' ')
                                        if all(k in col_normalized for k in keywords):
                                            try:
                                                val = row[col].strip().replace(',', '')
                                                if val == '.' or not val: return 0
                                                return int(float(val))
                                            except (ValueError, AttributeError):
                                                pass
                                    return 0

                                # For TFF: 
                                # non_commercial = Lev_Money + Other_Rept
                                # commercial = Dealer + Asset_Mgr (Commercials/Hedgers)
                                lev_long = get_val(row, ['lev', 'money', 'long'])
                                lev_short = get_val(row, ['lev', 'money', 'short'])
                                other_long = get_val(row, ['other', 'rept', 'long'])
                                other_short = get_val(row, ['other', 'rept', 'short'])
                                
                                dealer_long = get_val(row, ['dealer', 'long'])
                                dealer_short = get_val(row, ['dealer', 'short'])
                                asset_long = get_val(row, ['asset', 'mgr', 'long'])
                                asset_short = get_val(row, ['asset', 'mgr', 'short'])

                                nc_long = lev_long + other_long
                                nc_short = lev_short + other_short
                                c_long = dealer_long + asset_long
                                c_short = dealer_short + asset_short

                                data.append({
                                    'market': matched_name,
                                    'report_date': latest_date or '',
                                    'non_commercial_long': nc_long,
                                    'non_commercial_short': nc_short,
                                    'commercial_long': c_long,
                                    'commercial_short': c_short,
                                    'open_interest': get_val(row, ['open', 'interest']),
                                    'net_non_commercial': nc_long - nc_short,
                                    'net_commercial': c_long - c_short,
                                })


                        result = data if data else self._get_fallback_data()
                        if data:
                            self._cache["cot_data"] = result
                            self._cache_ts["cot_data"] = datetime.now().timestamp()
                        return result

        except Exception as e:
            logger.error(f"Error fetching COT data: {e}")
            # Return cached data if available, even if expired
            if cached:
                logger.info("Returning stale COT cache after fetch failure")
                return cached
            return self._get_fallback_data()

    def _get_fallback_data(self) -> List[dict]:
        """Fallback COT data when real fetch fails"""
        return [
            {'market': 'S&P 500', 'non_commercial_long': 250000, 'non_commercial_short': 100000, 'commercial_long': 150000, 'commercial_short': 300000, 'open_interest': 2500000, 'report_date': 'fallback', 'net_non_commercial': 150000, 'net_commercial': -150000},
            {'market': 'NASDAQ-100', 'non_commercial_long': 180000, 'non_commercial_short': 80000, 'commercial_long': 120000, 'commercial_short': 200000, 'open_interest': 1800000, 'report_date': 'fallback', 'net_non_commercial': 100000, 'net_commercial': -80000},
            {'market': 'Russell 2000', 'non_commercial_long': 45000, 'non_commercial_short': 65000, 'commercial_long': 80000, 'commercial_short': 60000, 'open_interest': 500000, 'report_date': 'fallback', 'net_non_commercial': -20000, 'net_commercial': 20000},
            {'market': 'Gold', 'non_commercial_long': 290000, 'non_commercial_short': 40000, 'commercial_long': 50000, 'commercial_short': 280000, 'open_interest': 550000, 'report_date': 'fallback', 'net_non_commercial': 250000, 'net_commercial': -230000},
            {'market': 'Crude Oil', 'non_commercial_long': 320000, 'non_commercial_short': 80000, 'commercial_long': 100000, 'commercial_short': 350000, 'open_interest': 1700000, 'report_date': 'fallback', 'net_non_commercial': 240000, 'net_commercial': -250000},
            {'market': '10Y T-Note', 'non_commercial_long': 400000, 'non_commercial_short': 600000, 'commercial_long': 550000, 'commercial_short': 350000, 'open_interest': 4200000, 'report_date': 'fallback', 'net_non_commercial': -200000, 'net_commercial': 200000},
            {'market': 'EUR/USD', 'non_commercial_long': 180000, 'non_commercial_short': 120000, 'commercial_long': 100000, 'commercial_short': 160000, 'open_interest': 700000, 'report_date': 'fallback', 'net_non_commercial': 60000, 'net_commercial': -60000},
            {'market': 'Bitcoin', 'non_commercial_long': 22000, 'non_commercial_short': 5000, 'commercial_long': 3000, 'commercial_short': 20000, 'open_interest': 35000, 'report_date': 'fallback', 'net_non_commercial': 17000, 'net_commercial': -17000},
        ]


cot_service = CotService()
