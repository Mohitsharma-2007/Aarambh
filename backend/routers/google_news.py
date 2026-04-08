"""routers/google_news.py"""
from fastapi import APIRouter, Query, Path
from scrapers import google_news as gn

router = APIRouter()

@router.get(
    "/search",
    summary="Search Google News via RSS",
    description="""
Search Google News. Returns articles with title, source, published date, URL, and summary.

**tip:** Use quotes for exact match: `q="AAPL" earnings`
""",
)
async def search(
    q:       str = Query(..., description='Search query e.g. "Apple earnings" or Bitcoin'),
    lang:    str = Query("en", description="Language code"),
    country: str = Query("US", description="Country: US | IN | GB | AU | CA | SG"),
    count:   int = Query(20,   description="Max articles (1–50)"),
):
    return await gn.search_news(q, lang, country, min(count, 50))


@router.get(
    "/topic/{topic}",
    summary="News by topic feed",
    description="""
Get news from a Google News topic feed.

**Topics:** `business` | `technology` | `science` | `health` |
`sports` | `world` | `finance` | `us` | `entertainment`
""",
)
async def topic(
    topic:   str = Path(..., description="business|technology|science|health|sports|world|finance|us"),
    lang:    str = Query("en"),
    country: str = Query("US"),
    count:   int = Query(30),
):
    return await gn.get_topic(topic, lang, country, min(count, 50))


@router.get(
    "/ticker/{ticker}",
    summary="News for a specific stock ticker",
)
async def ticker_news(
    ticker: str = Path(..., description="Stock ticker e.g. AAPL, TSLA"),
    count:  int = Query(20),
):
    return await gn.get_ticker_news(ticker, min(count, 50))


@router.get(
    "/headlines",
    summary="Top headlines from Google News",
)
async def headlines(
    country: str = Query("US", description="US | IN | GB | AU | CA"),
    lang:    str = Query("en"),
    count:   int = Query(30),
):
    return await gn.get_headlines(country, lang, min(count, 50))


@router.get(
    "/company/{company}",
    summary="News for a company by name",
)
async def company_news(
    company: str = Path(..., description="Company name e.g. Apple, Tesla"),
    ticker:  str = Query("", description="Optional ticker to broaden search"),
    count:   int = Query(20),
):
    return await gn.search_company_news(company, ticker, min(count, 50))
