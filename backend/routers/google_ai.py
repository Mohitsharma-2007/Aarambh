"""routers/google_ai.py"""
from fastapi import APIRouter, Query, Path
from scrapers import google_ai as gai

router = APIRouter()

@router.get(
    "/overview",
    summary="Google AI Overview / featured snippet",
    description="""
Fetch Google's AI Overview (SGE) or featured snippet for any search query.

Uses 4 extraction strategies:
1. `data-attrid` attribute scanning
2. CSS class selectors for known answer-box containers
3. `window.__WIZ_DATA__` JSON blob mining
4. Knowledge graph paragraph extraction

Note: AI Overview only appears for eligible queries — finance/stock queries
reliably produce knowledge panels even without the AI Overview block.
""",
)
async def ai_overview(
    q: str = Query(..., description="Any search query"),
):
    return await gai.get_ai_overview(q)


@router.get(
    "/finance-summary/{ticker}",
    summary="Google Finance knowledge panel + AI summary for a stock",
    description="""
Extracts the finance knowledge panel from Google Search for a stock ticker.

Equivalent to what SerpAPI's Google Finance API returns — but self-scraped.

Returns: price from panel, company name, key-value table data,
AI-generated summary (if present), and related questions.
""",
)
async def finance_summary(
    ticker: str = Path(..., description="Stock ticker e.g. AAPL, RELIANCE"),
):
    return await gai.get_finance_summary(ticker)
