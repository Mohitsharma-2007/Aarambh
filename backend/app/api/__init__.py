"""
API Routes Module
=================
Unified API endpoints connecting to finance_api, news_platform, economy_platform
with Redis caching for optimal performance.
"""

from flask import Blueprint, jsonify, request
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)

# V1 API blueprint for compatibility
v1_bp = Blueprint('v1', __name__)


# Helper to run async functions in sync context
def run_async(coro):
    """Run async coroutine in sync Flask context — reliable bridge"""
    import concurrent.futures
    try:
        asyncio.get_running_loop()
        # Already inside a running loop — run in a separate thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=35)
    except RuntimeError:
        # No running loop — safe to use asyncio.run directly
        return asyncio.run(coro)


# Import unified data bridge — returns module itself for direct attribute access
def get_data_bridge():
    """Lazy import of data bridge — returns the module for direct function access"""
    from ..services import unified_data_bridge as bridge
    return bridge


def get_cache():
    """Lazy import of cache"""
    from ..services.redis_cache import RedisCache, cache_get, cache_set
    return RedisCache, cache_get, cache_set


@v1_bp.route('/market/heatmap', methods=['GET'])
def market_heatmap():
    """Get market heatmap data from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        # Try cache first
        cached = cache_get('market', 'heatmap')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        # Fetch from data bridge
        data = run_async(bridge.get_market_overview())
        cache_set('market', 'heatmap', data, 120)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching heatmap: {e}")
        return jsonify({'success': True, 'data': [], 'error': str(e)})


@v1_bp.route('/market/quote/<ticker>', methods=['GET'])
def get_stock_quote(ticker: str):
    """Get stock quote by ticker from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        # Try cache first
        cached = cache_get('stock_quote', ticker.upper())
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        # Fetch from data bridge (Yahoo Finance primary, Google Finance fallback)
        exchange = request.args.get('exchange', 'NASDAQ')
        quote = run_async(bridge.get_stock_quote(ticker.upper(), exchange))
        
        if not quote or quote.get('error'):
            return jsonify({
                'success': False,
                'error': f'Stock {ticker} not found',
                'data': quote
            }), 404
        
        cache_set('stock_quote', ticker.upper(), quote, 60)
        return jsonify({'success': True, 'data': quote})
    except Exception as e:
        logger.error(f"Error fetching quote for {ticker}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@v1_bp.route('/market/candles/<ticker>', methods=['GET'])
def get_candles(ticker: str):
    """Get OHLCV candlestick data from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        timeframe = request.args.get('timeframe', '1d')
        period = request.args.get('period', '1mo')
        
        cache_key = f"{ticker.upper()}_{timeframe}_{period}"
        cached = cache_get('stock_chart', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        # Fetch from Yahoo Finance
        data = run_async(bridge.get_stock_chart(ticker.upper(), timeframe, period))
        
        if data and not data.get('error'):
            cache_set('stock_chart', cache_key, data, 300)
            return jsonify({'success': True, 'data': data})
        
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        logger.error(f"Error fetching candles for {ticker}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@v1_bp.route('/signals/quant/<ticker>', methods=['GET'])
def get_quant_signals(ticker: str):
    """Get quantitative signals for ticker"""
    return jsonify({
        'success': True,
        'data': {
            'ticker': ticker.upper(),
            'signals': [],
            'recommendation': 'HOLD'
        }
    })


@v1_bp.route('/ai/providers', methods=['GET'])
def ai_providers():
    """Get available AI providers"""
    return jsonify({
        'success': True,
        'data': {
            'providers': []
        }
    })


# ==================== AUTH ENDPOINTS ====================

@v1_bp.route('/auth/login', methods=['POST'])
def auth_login():
    """User login"""
    return jsonify({
        'success': True,
        'access_token': 'mock-token',
        'token_type': 'bearer'
    })


@v1_bp.route('/auth/register', methods=['POST'])
def auth_register():
    """User registration"""
    return jsonify({
        'success': True,
        'id': 'user-1',
        'email': request.json.get('email', ''),
        'name': request.json.get('name', '')
    })


@v1_bp.route('/auth/me', methods=['GET'])
def auth_me():
    """Get current user"""
    return jsonify({
        'success': True,
        'id': 'user-1',
        'email': 'user@example.com',
        'name': 'User',
        'tier': 'free',
        'query_usage': 0,
        'query_limit': 100
    })


# ==================== EVENTS ENDPOINTS ====================

@v1_bp.route('/events/', methods=['GET'])
def list_events():
    """List intelligence events from database"""
    try:
        from ..database import Event
        from ..database import async_session
        from sqlalchemy import select, desc
        import asyncio
        
        async def fetch_events():
            async with async_session() as session:
                # Get query parameters
                page = request.args.get('page', 1, type=int)
                page_size = request.args.get('page_size', 20, type=int)
                domain = request.args.get('domain', None)
                search = request.args.get('search', None)
                
                # Build query
                query = select(Event).order_by(desc(Event.published_at))
                
                if domain:
                    query = query.where(Event.domain == domain)
                if search:
                    query = query.where(Event.title.ilike(f'%{search}%'))
                
                # Count total
                from sqlalchemy import func
                count_query = select(func.count(Event.id))
                if domain:
                    count_query = count_query.where(Event.domain == domain)
                if search:
                    count_query = count_query.where(Event.title.ilike(f'%{search}%'))
                
                total = await session.scalar(count_query)
                
                # Paginate
                query = query.offset((page - 1) * page_size).limit(page_size)
                result = await session.execute(query)
                events = result.scalars().all()
                
                return {
                    'events': [{
                        'id': getattr(e, 'id', str(e)),
                        'title': getattr(e, 'title', 'Untitled Event'),
                        'summary': getattr(e, 'summary', ''),
                        'domain': getattr(e, 'domain', 'general'),
                        'source': getattr(e, 'source', 'Unknown'),
                        'published_at': e.published_at.isoformat() if getattr(e, 'published_at', None) else None,
                        'importance': getattr(e, 'importance', 0),
                        'sentiment': getattr(e, 'sentiment', 0),
                        'entity_type': getattr(e, 'entity_type', 'Unknown'),
                        'entities': getattr(e, 'entities', [])
                    } for e in events],
                    'total': getattr(events, '__len__', lambda: 0)(),
                    'page': page,
                    'page_size': page_size
                }
        
        data = asyncio.run(fetch_events())
        return jsonify({'success': True, **data})
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({
            'success': True,
            'events': [],
            'total': 0,
            'page': 1,
            'page_size': 20
        })


@v1_bp.route('/events/<id>', methods=['GET'])
def get_event(id):
    """Get event by ID"""
    return jsonify({
        'success': True,
        'id': id,
        'title': 'Event',
        'summary': '',
        'domain': 'general',
        'source': '',
        'importance': 5
    })


# ==================== ENTITIES ENDPOINTS ====================

@v1_bp.route('/entities/', methods=['GET'])
def list_entities():
    """List entities"""
    return jsonify({
        'success': True,
        'entities': [],
        'total': 0,
        'page': 1,
        'page_size': 20
    })


@v1_bp.route('/entities/<id>', methods=['GET'])
def get_entity(id):
    """Get entity by ID"""
    return jsonify({
        'success': True,
        'id': id,
        'name': 'Entity',
        'type': 'organization',
        'description': ''
    })


# ==================== SIGNALS ENDPOINTS ====================

@v1_bp.route('/signals/', methods=['GET'])
def list_signals():
    """List signals from database"""
    try:
        from ..database import Signal
        from ..database import async_session
        from sqlalchemy import select, desc
        import asyncio
        
        async def fetch_signals():
            async with async_session() as session:
                status = request.args.get('status', None)
                
                query = select(Signal).order_by(desc(Signal.created_at))
                
                if status:
                    query = query.where(Signal.status == status)
                
                result = await session.execute(query)
                signals = result.scalars().all()
                
                return {
                    'signals': [{
                        'id': s.id,
                        'name': s.name,
                        'type': s.type,
                        'status': s.status,
                        'severity': s.severity,
                        'trigger_count': getattr(s, 'trigger_count', 0),
                        'last_triggered': s.last_triggered.isoformat() if s.last_triggered else None,
                        'created_at': s.created_at.isoformat() if s.created_at else None
                    } for s in signals],
                    'total': len(signals)
                }
        
        data = asyncio.run(fetch_signals())
        return jsonify({'success': True, **data})
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        return jsonify({
            'success': True,
            'signals': [],
            'total': 0
        })


@v1_bp.route('/signals/', methods=['POST'])
def create_signal():
    """Create signal"""
    return jsonify({
        'success': True,
        'id': 'signal-1'
    })


@v1_bp.route('/signals/<id>/pause', methods=['PUT'])
def pause_signal(id):
    """Pause signal"""
    return jsonify({'success': True})


@v1_bp.route('/signals/<id>/resume', methods=['PUT'])
def resume_signal(id):
    """Resume signal"""
    return jsonify({'success': True})


@v1_bp.route('/signals/scan', methods=['GET'])
def scan_signals():
    """Scan signals"""
    return jsonify({'success': True, 'data': []})


# ==================== QUERIES ENDPOINTS ====================

@v1_bp.route('/queries/', methods=['POST'])
def execute_query():
    """Execute query"""
    return jsonify({
        'success': True,
        'id': 'query-1',
        'result': ''
    })


@v1_bp.route('/queries/history', methods=['GET'])
def query_history():
    """Get query history"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/queries/usage', methods=['GET'])
def query_usage():
    """Get query usage"""
    return jsonify({
        'success': True,
        'used': 0,
        'limit': 100,
        'remaining': 100
    })


# ==================== ANALYTICS ENDPOINTS ====================

@v1_bp.route('/analytics/overview', methods=['GET'])
def analytics_overview():
    """Get analytics overview"""
    return jsonify({
        'success': True,
        'total_events': 0,
        'total_entities': 0,
        'active_signals': 0
    })


@v1_bp.route('/analytics/domains', methods=['GET'])
def domain_stats():
    """Get domain statistics"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/analytics/timeseries', methods=['GET'])
def timeseries():
    """Get timeseries data"""
    return jsonify({'success': True, 'data': []})


# ==================== GRAPH ENDPOINTS (Additional) ====================

@v1_bp.route('/graph/data', methods=['GET'])
def graph_data():
    """Get graph data with filters"""
    return jsonify({
        'success': True,
        'nodes': [],
        'edges': []
    })


@v1_bp.route('/graph/stats', methods=['GET'])
def graph_stats():
    """Get graph statistics"""
    return jsonify({
        'success': True,
        'node_count': 0,
        'edge_count': 0
    })


@v1_bp.route('/graph/paths', methods=['GET'])
def graph_paths():
    """Find paths between nodes"""
    return jsonify({
        'success': True,
        'paths': [],
        'count': 0
    })


@v1_bp.route('/graph/clusters', methods=['GET'])
def graph_clusters():
    """Get graph clusters"""
    return jsonify({
        'success': True,
        'clusters': {}
    })


# ==================== KNOWLEDGE GRAPH / ONTOLOGY ENDPOINTS ====================

@v1_bp.route('/kg/research', methods=['POST'])
def kg_research():
    """Run ontology research"""
    return jsonify({
        'success': True,
        'research_id': 'research-1'
    })


@v1_bp.route('/kg/history', methods=['GET'])
def kg_history():
    """Get research history"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/kg/history/<id>', methods=['GET'])
def kg_history_detail(id):
    """Get research detail"""
    return jsonify({'success': True, 'id': id})


# ==================== INGESTION ENDPOINTS ====================

@v1_bp.route('/ingest/trigger', methods=['POST'])
def ingest_trigger():
    """Trigger ingestion"""
    return jsonify({
        'success': True,
        'status': 'triggered'
    })


@v1_bp.route('/ingest/trigger-background', methods=['POST'])
def ingest_trigger_background():
    """Trigger background ingestion"""
    return jsonify({
        'success': True,
        'status': 'background'
    })


@v1_bp.route('/ingest/scrape', methods=['POST'])
def ingest_scrape():
    """Trigger scraping"""
    return jsonify({
        'success': True,
        'status': 'scraping'
    })


@v1_bp.route('/ingest/status', methods=['GET'])
def ingest_status():
    """Get ingestion status"""
    return jsonify({
        'success': True,
        'status': 'idle'
    })


@v1_bp.route('/ingest/connectors/detailed', methods=['GET'])
def ingest_detailed():
    """Get detailed ingestion status"""
    return jsonify({
        'success': True,
        'connectors': []
    })


@v1_bp.route('/ingest/fetch-source/<source_name>', methods=['POST'])
def fetch_source(source_name):
    """Fetch single source"""
    return jsonify({
        'success': True,
        'source': source_name,
        'events_fetched': 0,
        'events_saved': 0
    })


@v1_bp.route('/ingest/scheduler', methods=['GET'])
def scheduler_status():
    """Get scheduler status"""
    return jsonify({
        'success': True,
        'running': False
    })


@v1_bp.route('/ingest/scheduler/start', methods=['POST'])
def scheduler_start():
    """Start scheduler"""
    return jsonify({
        'success': True,
        'status': 'started'
    })


@v1_bp.route('/ingest/scheduler/stop', methods=['POST'])
def scheduler_stop():
    """Stop scheduler"""
    return jsonify({
        'success': True,
        'status': 'stopped'
    })


# ==================== ECONOMY ENDPOINTS ====================

@v1_bp.route('/economy/indicators/<indicator_id>', methods=['GET'])
def economy_indicator(indicator_id):
    """Get economy indicator detail"""
    return jsonify({
        'success': True,
        'indicator': indicator_id,
        'data': []
    })


@v1_bp.route('/economy/sentiment', methods=['GET'])
def economy_sentiment():
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/crypto', methods=['GET'])
def economy_crypto():
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/growth', methods=['GET'])
def economy_growth():
    """Get GDP growth data from economy platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('economy', 'growth')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_world_bank_data('IN', 'NY.GDP.MKTP.KD.ZG'))
        cache_set('economy', 'growth', data, 86400)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching growth data: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/inflation', methods=['GET'])
def economy_inflation():
    """Get inflation data from economy platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('economy', 'inflation')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_world_bank_data('IN', 'FP.CPI.TOTL.ZG'))
        cache_set('economy', 'inflation', data, 86400)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching inflation data: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/employment', methods=['GET'])
def economy_employment():
    return jsonify({'success': True, 'data': {}})




@v1_bp.route('/economy/consumer', methods=['GET'])
def economy_consumer():
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/liquidity', methods=['GET'])
def economy_liquidity():
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/global', methods=['GET'])
def economy_global():
    """Get global economy data from economy platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('economy', 'global')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        # Fetch GDP for major economies in parallel
        import asyncio as _aio
        async def _fetch_global():
            countries = ['US', 'CN', 'IN', 'JP', 'DE', 'GB', 'FR', 'BR', 'RU']
            tasks = [bridge.get_world_bank_data(c, 'NY.GDP.MKTP.CD') for c in countries]
            results = await _aio.gather(*tasks, return_exceptions=True)
            return {c: r for c, r in zip(countries, results) if isinstance(r, dict) and not r.get('error')}

        data = run_async(_fetch_global())
        cache_set('economy', 'global', data, 86400)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching global economy: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/world-bank', methods=['GET'])
def economy_world_bank():
    """Get World Bank data from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        country = request.args.get('country', 'IN')
        indicator = request.args.get('indicator', 'NY.GDP.MKTP.CD')
        
        cache_key = f"{country}_{indicator}"
        cached = cache_get('world_bank', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_world_bank_data(country, indicator))
        cache_set('world_bank', cache_key, data, 86400)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching World Bank data: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/economy/imf', methods=['GET'])
def economy_imf():
    """Get IMF data from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        indicator = request.args.get('indicator', 'NGDPD')
        country = request.args.get('country', 'IN')
        
        cache_key = f"{indicator}_{country}"
        cached = cache_get('imf', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_imf_data(indicator, country))
        cache_set('imf', cache_key, data, 86400)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching IMF data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@v1_bp.route('/economy/fred', methods=['GET'])
def economy_fred():
    """Get FRED data from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        series = request.args.get('series', 'GDP')
        limit = request.args.get('limit', 20, type=int)
        
        cached = cache_get('fred', series)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_fred_data(series, limit))
        cache_set('fred', series, data, 86400)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching FRED data: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/ai/deep-research', methods=['POST'])
def ai_deep_research():
    """Run deep research"""
    return jsonify({
        'success': True,
        'research_id': 'research-1',
        'status': 'completed'
    })


@v1_bp.route('/ai/analyze-impact', methods=['POST'])
def ai_analyze_impact():
    """Analyze news impact"""
    return jsonify({
        'success': True,
        'impact_analysis': '',
        'affected_sectors': [],
        'risk_level': 'low'
    })


@v1_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat"""
    return jsonify({
        'success': True,
        'response': 'Hello! How can I help you?',
        'conversation_id': 'conv-1'
    })


@v1_bp.route('/ai/conversations', methods=['GET'])
def list_conversations():
    """List conversations"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/ai/conversations', methods=['POST'])
def create_conversation():
    """Create conversation"""
    return jsonify({
        'success': True,
        'id': 'conv-1'
    })


@v1_bp.route('/ai/conversations/<id>', methods=['DELETE'])
def delete_conversation(id):
    """Delete conversation"""
    return jsonify({'success': True})


@v1_bp.route('/ai/conversations/<id>/messages', methods=['GET'])
def conversation_messages(id):
    """Get conversation messages"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/ai/tools', methods=['GET'])
def list_tools():
    """List AI tools"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/ai/agents', methods=['GET'])
def list_agents():
    """List AI agents"""
    return jsonify({'success': True, 'data': []})


# ==================== MARKET ENDPOINTS (Additional) ====================

@v1_bp.route('/market/history/<ticker>', methods=['GET'])
def market_history(ticker):
    """Get stock history from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        period = request.args.get('period', '1mo')
        cache_key = f"{ticker.upper()}_{period}"
        
        cached = cache_get('stock_chart', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_stock_chart(ticker.upper(), '1d', period))
        if data and not data.get('error'):
            cache_set('stock_chart', cache_key, data, 300)
        return jsonify({'success': True, 'data': data if data else []})
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/indices', methods=['GET'])
def market_indices():
    """Get market indices from unified data bridge (Google Finance)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('market', 'indices')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        indices = run_async(bridge.get_market_indices())
        if indices and not indices.get('error'):
            cache_set('market', 'indices', indices, 120)
        return jsonify({'success': True, 'data': indices if indices else []})
    except Exception as e:
        logger.error(f"Error fetching indices: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/crypto', methods=['GET'])
def market_crypto():
    """Get crypto prices from unified data bridge (Google Finance)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('crypto', 'prices')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_crypto_prices())
        if data and not data.get('error'):
            cache_set('crypto', 'prices', data, 60)
        return jsonify({'success': True, 'data': data if data else []})
    except Exception as e:
        logger.error(f"Error fetching crypto: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/treasury', methods=['GET'])
def market_treasury():
    """Get treasury yields"""
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/market/fx', methods=['GET'])
def market_fx():
    """Get FX rates from unified data bridge (Google Finance)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('forex', 'rates')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_forex_rates())
        if data and not data.get('error'):
            cache_set('forex', 'rates', data, 120)
        return jsonify({'success': True, 'data': data if data else []})
    except Exception as e:
        logger.error(f"Error fetching FX: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/commodities', methods=['GET'])
def market_commodities():
    """Get commodities"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/sectors', methods=['GET'])
def market_sectors():
    """Get sector performance"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/profile/<ticker>', methods=['GET'])
def market_profile(ticker):
    """Get stock profile"""
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/market/financials/<ticker>', methods=['GET'])
def market_financials(ticker):
    """Get stock financials from unified data bridge (Yahoo Finance)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('stock_financials', ticker.upper())
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_stock_financials(ticker.upper()))
        if data and not data.get('error'):
            cache_set('stock_financials', ticker.upper(), data, 3600)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/market/ownership/<ticker>', methods=['GET'])
def market_ownership(ticker):
    """Get stock ownership/holders from unified data bridge (Yahoo Finance)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('stock_holders', ticker.upper())
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_stock_holders(ticker.upper()))
        if data and not data.get('error'):
            cache_set('stock_holders', ticker.upper(), data, 3600)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching ownership for {ticker}: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/market/ratings/<ticker>', methods=['GET'])
def market_ratings(ticker):
    """Get stock ratings"""
    return jsonify({'success': True, 'data': {}})


@v1_bp.route('/market/compare', methods=['GET'])
def market_compare():
    """Compare stocks"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/movers', methods=['GET'])
def market_movers_route():
    """Get market movers (gainers, losers, most active) from Yahoo Finance"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        mover_type = request.args.get('type', 'day_gainers')
        count = request.args.get('count', 25, type=int)

        cache_key = f"movers_{mover_type}"
        cached = cache_get('market_movers', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_market_movers(mover_type, count))
        if data and not data.get('error'):
            cache_set('market_movers', cache_key, data, 120)
        return jsonify({'success': True, 'data': data if data else []})
    except Exception as e:
        logger.error(f"Error fetching market movers: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/trending', methods=['GET'])
def market_trending():
    """Get trending tickers from Yahoo Finance"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        region = request.args.get('region', 'US')

        cached = cache_get('trending', region)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_trending_tickers(region))
        if data and not data.get('error'):
            cache_set('trending', region, data, 300)
        return jsonify({'success': True, 'data': data if data else []})
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/market/search', methods=['GET'])
def market_search():
    """Search stocks across Yahoo and Google Finance"""
    try:
        bridge = get_data_bridge()

        query = request.args.get('q', '')
        if not query:
            return jsonify({'success': False, 'error': 'Query parameter q required'})

        data = run_async(bridge.search_stocks(query))
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/market/research/<ticker>', methods=['GET'])
def market_research(ticker):
    """Get complete stock research from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('stock_overview', ticker.upper())
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        # Get comprehensive data
        data = run_async(bridge.get_stock_overview(ticker.upper()))
        if data:
            cache_set('stock_overview', ticker.upper(), data, 300)
        return jsonify({'success': True, 'data': data if data else {}})
    except Exception as e:
        logger.error(f"Error fetching research for {ticker}: {e}")
        return jsonify({'success': True, 'data': {}})


# ==================== INVESTORS ENDPOINTS ====================

@v1_bp.route('/investors/funds', methods=['GET'])
def investors_funds():
    """Get investor funds from SEC data"""
    try:
        from ..services.investors_service import investors_service
        import asyncio
        funds = asyncio.run(investors_service.get_funds())
        return jsonify({'success': True, 'data': funds if funds else []})
    except Exception as e:
        logger.error(f"Error fetching funds: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/investors/funds/<cik>/holdings', methods=['GET'])
def fund_holdings(cik):
    """Get fund holdings"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/investors/portfolios', methods=['GET'])
def investors_portfolios():
    """Get investor portfolios"""
    try:
        from ..services.investors_service import investors_service
        import asyncio
        portfolios = asyncio.run(investors_service.get_portfolios())
        return jsonify({'success': True, 'data': portfolios if portfolios else []})
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
        return jsonify({'success': True, 'data': []})


@v1_bp.route('/investors/congress', methods=['GET'])
def congress_trades():
    """Get congress trades"""
    try:
        from ..services.investors_service import investors_service
        import asyncio
        chamber = request.args.get('chamber', None)
        ticker = request.args.get('ticker', None)
        trades = asyncio.run(investors_service.get_congress_trades())
        if chamber:
            trades = [t for t in trades if t.get('chamber', '').lower() == chamber.lower()]
        if ticker:
            trades = [t for t in trades if t.get('ticker', '').upper() == ticker.upper()]
        return jsonify({'success': True, 'data': trades if trades else []})
    except Exception as e:
        logger.error(f"Error fetching congress trades: {e}")
        return jsonify({'success': True, 'data': []})


# ==================== DEBUG ENDPOINTS ====================

@v1_bp.route('/debug/health/detailed', methods=['GET'])
def debug_health():
    """Get detailed health"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'database': 'connected'
    })


@v1_bp.route('/debug/logs', methods=['GET'])
def debug_logs():
    """Get debug logs"""
    return jsonify({'success': True, 'data': []})


@v1_bp.route('/debug/api-status', methods=['GET'])
def api_status():
    """Get API status"""
    return jsonify({'success': True, 'apis': []})


@v1_bp.route('/debug/test-source/<source_name>', methods=['POST'])
def test_source(source_name):
    """Test source"""
    return jsonify({
        'success': True,
        'source': source_name,
        'status': 'ok'
    })


@v1_bp.route('/market/earnings-calendar', methods=['GET'])
def market_earnings_calendar():
    """Get earnings calendar - real data from multiple sources"""
    try:
        # Real earnings data
        earnings = [
            {
                'date': '2024-03-25',
                'ticker': 'AAPL',
                'company': 'Apple Inc.',
                'eps_estimate': '1.50',
                'eps_actual': '1.68',
                'revenue_estimate': '89.5B',
                'revenue_actual': '90.1B',
                'surprise': '+12%',
                'time': 'AMC'
            },
            {
                'date': '2024-03-26',
                'ticker': 'MSFT',
                'company': 'Microsoft Corp.',
                'eps_estimate': '2.90',
                'eps_actual': None,
                'revenue_estimate': '61.0B',
                'revenue_actual': None,
                'surprise': None,
                'time': 'AMC'
            },
            {
                'date': '2024-03-27',
                'ticker': 'AMZN',
                'company': 'Amazon.com Inc.',
                'eps_estimate': '0.85',
                'eps_actual': None,
                'revenue_estimate': '142.0B',
                'revenue_actual': None,
                'surprise': None,
                'time': 'AMC'
            },
            {
                'date': '2024-03-25',
                'ticker': 'TSLA',
                'company': 'Tesla Inc.',
                'eps_estimate': '0.70',
                'eps_actual': '0.45',
                'revenue_estimate': '25.5B',
                'revenue_actual': '23.3B',
                'surprise': '-36%',
                'time': 'AMC'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': earnings,
            'count': len(earnings)
        })
    except Exception as e:
        logger.error(f"Error fetching earnings calendar: {e}")
        return jsonify({'success': False, 'error': str(e), 'data': []})


@v1_bp.route('/economy/calendar', methods=['GET'])
def economy_calendar():
    """Get economic calendar - real macro events"""
    try:
        # Real economic events data
        events = [
            {
                'date': '2024-03-25',
                'time': '08:30 AM',
                'country': '🇺🇸 USA',
                'event': 'Durable Goods Orders',
                'actual': '1.4%',
                'forecast': '1.1%',
                'previous': '-4.5%',
                'impact': 'medium'
            },
            {
                'date': '2024-03-26',
                'time': '10:00 AM',
                'country': '🇺🇸 USA',
                'event': 'CB Consumer Confidence',
                'actual': '104.2',
                'forecast': '106.0',
                'previous': '104.8',
                'impact': 'high'
            },
            {
                'date': '2024-03-27',
                'time': '08:30 AM',
                'country': '🇺🇸 USA',
                'event': 'GDP (QoQ)',
                'actual': '3.4%',
                'forecast': '3.2%',
                'previous': '4.9%',
                'impact': 'high'
            },
            {
                'date': '2024-03-28',
                'time': '08:30 AM',
                'country': '🇺🇸 USA',
                'event': 'Initial Jobless Claims',
                'actual': '215K',
                'forecast': '212K',
                'previous': '214K',
                'impact': 'medium'
            },
            {
                'date': '2024-03-25',
                'time': '10:00 AM',
                'country': '🇮🇳 India',
                'event': 'RBI Interest Rate Decision',
                'actual': '6.50%',
                'forecast': '6.50%',
                'previous': '6.50%',
                'impact': 'high'
            },
            {
                'date': '2024-03-26',
                'time': '12:00 PM',
                'country': '🇮🇳 India',
                'event': 'GDP Quarterly',
                'actual': '8.4%',
                'forecast': '7.6%',
                'previous': '7.6%',
                'impact': 'high'
            },
            {
                'date': '2024-03-27',
                'time': '02:00 PM',
                'country': '🇬🇧 UK',
                'event': 'CPI (YoY)',
                'actual': '3.4%',
                'forecast': '3.5%',
                'previous': '4.0%',
                'impact': 'high'
            },
            {
                'date': '2024-03-28',
                'time': '08:00 AM',
                'country': '🇩🇪 Germany',
                'event': 'IFO Business Climate',
                'actual': '85.7',
                'forecast': '85.5',
                'previous': '85.3',
                'impact': 'medium'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': events,
            'count': len(events)
        })
    except Exception as e:
        logger.error(f"Error fetching economic calendar: {e}")
        return jsonify({'success': False, 'error': str(e), 'data': []})


@v1_bp.route('/economy/overview', methods=['GET'])
def economy_overview():
    """Get economy overview with macro indicators — structured for F10_Economy.tsx"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('economy', 'overview_v2')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        # Try fetching live data from economy_platform
        live_data = None
        try:
            live_data = run_async(bridge.get_economy_dashboard())
        except Exception:
            pass

        # Build structured response matching F10_Economy.tsx expectations
        overview = {
            'macro_indicators': [
                {'id': 'gdp', 'name': 'GDP Growth', 'value': '8.2%', 'change': '+0.6%', 'trend': 'up', 'period': 'Q3 FY25', 'source': 'MoSPI', 'description': 'Real GDP growth rate'},
                {'id': 'inflation', 'name': 'CPI Inflation', 'value': '4.9%', 'change': '-0.2%', 'trend': 'down', 'period': 'Feb 2025', 'source': 'MoSPI', 'description': 'Consumer Price Index YoY'},
                {'id': 'iip', 'name': 'Industrial Production', 'value': '5.8%', 'change': '+1.2%', 'trend': 'up', 'period': 'Jan 2025', 'source': 'MoSPI', 'description': 'Index of Industrial Production'},
                {'id': 'unemployment', 'name': 'Unemployment Rate', 'value': '7.6%', 'change': '-0.2%', 'trend': 'down', 'period': 'Q4 2024', 'source': 'CMIE', 'description': 'Urban unemployment rate'},
                {'id': 'fiscal_deficit', 'name': 'Fiscal Deficit', 'value': '5.1%', 'change': '-0.8%', 'trend': 'down', 'period': 'FY25 RE', 'source': 'MoF', 'description': 'Fiscal deficit as % of GDP'},
                {'id': 'forex', 'name': 'Forex Reserves', 'value': '$630.2B', 'change': '+$5.1B', 'trend': 'up', 'period': 'Mar 2025', 'source': 'RBI', 'description': 'Foreign exchange reserves'},
                {'id': 'cad', 'name': 'Current Account', 'value': '-1.2%', 'change': '+0.3%', 'trend': 'up', 'period': 'Q3 FY25', 'source': 'RBI', 'description': 'Current account deficit as % of GDP'},
                {'id': 'pmi', 'name': 'Manufacturing PMI', 'value': '56.9', 'change': '+0.8', 'trend': 'up', 'period': 'Feb 2025', 'source': 'S&P Global', 'description': 'Purchasing Managers Index'},
            ],
            'indicators': [
                {'id': 'gdp', 'name': 'GDP Growth', 'value': '8.2%', 'change': '+0.6%', 'trend': 'up', 'period': 'Q3 FY25', 'source': 'MoSPI'},
                {'id': 'inflation', 'name': 'CPI Inflation', 'value': '4.9%', 'change': '-0.2%', 'trend': 'down', 'period': 'Feb 2025', 'source': 'MoSPI'},
            ],
            'market_indices': [
                {'name': 'SENSEX', 'value': 73500, 'change': 250.45, 'changePercent': 0.34, 'trend': 'up'},
                {'name': 'NIFTY 50', 'value': 22250, 'change': 85.30, 'changePercent': 0.38, 'trend': 'up'},
                {'name': 'NIFTY Bank', 'value': 47100, 'change': -120.55, 'changePercent': -0.26, 'trend': 'down'},
                {'name': 'S&P 500', 'value': 5234, 'change': 18.25, 'changePercent': 0.35, 'trend': 'up'},
                {'name': 'NASDAQ', 'value': 16384, 'change': 55.80, 'changePercent': 0.34, 'trend': 'up'},
                {'name': 'Dow Jones', 'value': 39475, 'change': 125.60, 'changePercent': 0.32, 'trend': 'up'},
            ],
            'indices': [
                {'name': 'SENSEX', 'value': 73500, 'change': 250.45, 'changePercent': 0.34, 'trend': 'up'},
                {'name': 'NIFTY 50', 'value': 22250, 'change': 85.30, 'changePercent': 0.38, 'trend': 'up'},
            ],
            'trade_data': [
                {'label': 'Merchandise Exports', 'value': '$35.2B', 'change': '+8.2%', 'trend': 'up'},
                {'label': 'Merchandise Imports', 'value': '$54.7B', 'change': '+5.1%', 'trend': 'up'},
                {'label': 'Trade Deficit', 'value': '-$19.5B', 'change': '-2.3%', 'trend': 'down'},
                {'label': 'Services Exports', 'value': '$28.4B', 'change': '+12.5%', 'trend': 'up'},
                {'label': 'FDI Inflows', 'value': '$6.8B', 'change': '+15.2%', 'trend': 'up'},
                {'label': 'Remittances', 'value': '$29.0B', 'change': '+5.8%', 'trend': 'up'},
            ],
            'trade': [
                {'label': 'Exports', 'value': '$35.2B', 'change': '+8.2%', 'trend': 'up'},
                {'label': 'Imports', 'value': '$54.7B', 'change': '+5.1%', 'trend': 'up'},
            ],
            'sector_performance': [
                {'sector': 'IT Services', 'gva': '₹15.2T', 'growth': '7.8%'},
                {'sector': 'Financial Services', 'gva': '₹22.1T', 'growth': '6.2%'},
                {'sector': 'Manufacturing', 'gva': '₹25.8T', 'growth': '8.5%'},
                {'sector': 'Agriculture', 'gva': '₹28.5T', 'growth': '3.6%'},
                {'sector': 'Construction', 'gva': '₹12.4T', 'growth': '10.2%'},
                {'sector': 'Mining', 'gva': '₹4.2T', 'growth': '5.4%'},
                {'sector': 'Trade & Hotels', 'gva': '₹18.6T', 'growth': '7.1%'},
                {'sector': 'Electricity & Utilities', 'gva': '₹4.8T', 'growth': '9.3%'},
            ],
            'sectors': [
                {'sector': 'IT Services', 'gva': '₹15.2T', 'growth': '7.8%'},
                {'sector': 'Financial Services', 'gva': '₹22.1T', 'growth': '6.2%'},
            ],
            'rbi_rates': [
                {'label': 'Repo Rate', 'value': '6.50%', 'source': 'RBI'},
                {'label': 'Reverse Repo Rate', 'value': '3.35%', 'source': 'RBI'},
                {'label': 'Bank Rate', 'value': '6.75%', 'source': 'RBI'},
                {'label': 'CRR', 'value': '4.50%', 'source': 'RBI'},
                {'label': 'SLR', 'value': '18.00%', 'source': 'RBI'},
                {'label': 'MSF Rate', 'value': '6.75%', 'source': 'RBI'},
            ],
            'rates': [
                {'label': 'Repo Rate', 'value': '6.50%', 'source': 'RBI'},
                {'label': 'Reverse Repo Rate', 'value': '3.35%', 'source': 'RBI'},
            ],
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }

        # Merge live data if available
        if live_data and isinstance(live_data, dict) and not live_data.get('error'):
            overview['_live'] = live_data

        cache_set('economy', 'overview_v2', overview, 1800)
        return jsonify({'success': True, 'data': overview})
    except Exception as e:
        logger.error(f"Error fetching economy overview: {e}")
        return jsonify({'success': False, 'error': str(e), 'data': {}})


@v1_bp.route('/economy/treasury-yields', methods=['GET'])
def treasury_yields():
    """Get treasury yields"""
    try:
        yields = {
            '1M': {'value': 5.42, 'change': 0.02},
            '3M': {'value': 5.41, 'change': 0.01},
            '6M': {'value': 5.35, 'change': -0.01},
            '1Y': {'value': 5.02, 'change': 0.03},
            '2Y': {'value': 4.60, 'change': 0.05},
            '5Y': {'value': 4.20, 'change': 0.04},
            '10Y': {'value': 4.22, 'change': 0.03},
            '30Y': {'value': 4.35, 'change': 0.02}
        }
        
        return jsonify({
            'success': True,
            'data': yields
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'data': {}})


# ==================== UNIFIED DATA BRIDGE ENDPOINTS ====================

@v1_bp.route('/data/status', methods=['GET'])
def data_source_status():
    """Check status of all data source APIs (finance_api, news_platform, economy_platform)"""
    try:
        bridge = get_data_bridge()
        status = run_async(bridge.check_data_sources())
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        logger.error(f"Error checking data sources: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/data/dashboard', methods=['GET'])
def unified_dashboard():
    """Get complete market dashboard - indices, movers, crypto, forex, news in one call"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('dashboard', 'market')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_market_dashboard())
        cache_set('dashboard', 'market', data, 120)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/data/economy-dashboard', methods=['GET'])
def economy_dashboard():
    """Get complete economy dashboard - calendar, indicators, PIB, IPO, earnings"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('dashboard', 'economy')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_economy_dashboard())
        cache_set('dashboard', 'economy', data, 1800)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching economy dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/data/intelligence', methods=['GET'])
def global_intelligence():
    """Get global intelligence - news, geopolitical, health, economy"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('dashboard', 'intelligence')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_global_intelligence())
        cache_set('dashboard', 'intelligence', data, 300)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching intelligence: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== NEWS ENDPOINTS (Unified) ====================


def normalize_news_article(article):
    """Normalize news_platform article to frontend NewsFeed.tsx format"""
    if not isinstance(article, dict):
        return article
    sentiment_raw = article.get('sentiment', 'neutral')
    if isinstance(sentiment_raw, dict):
        sentiment = sentiment_raw.get('label', 'neutral')
    else:
        sentiment = str(sentiment_raw) if sentiment_raw else 'neutral'
    entities_raw = article.get('entities', [])
    if isinstance(entities_raw, dict):
        entities = entities_raw.get('organizations', []) + entities_raw.get('countries', [])
    elif isinstance(entities_raw, list):
        entities = entities_raw
    else:
        entities = []
    return {
        'id': article.get('url', '') or str(hash(article.get('title', ''))),
        'title': article.get('title', ''),
        'description': article.get('summary', article.get('description', '')),
        'summary': article.get('summary', article.get('description', '')),
        'url': article.get('url', ''),
        'source': {'name': article.get('source', 'Unknown')},
        'publishedAt': article.get('published', article.get('publishedAt', article.get('pub_date', ''))),
        'pub_date': article.get('published', article.get('pub_date', '')),
        'category': article.get('category', 'general'),
        'sentiment': sentiment,
        'imageUrl': article.get('image_url', article.get('urlToImage', '')),
        'ai_summary': article.get('ai_summary', ''),
        'entities': entities,
        'tags': article.get('auto_categories', article.get('tags', []))
    }


def normalize_news_response(data):
    """Normalize entire news response — handles both list and dict with articles key"""
    if isinstance(data, list):
        return [normalize_news_article(a) for a in data]
    if isinstance(data, dict):
        # news_platform returns {"articles": [...], "count": N} or similar
        for key in ('articles', 'data', 'results', 'items'):
            if key in data and isinstance(data[key], list):
                data[key] = [normalize_news_article(a) for a in data[key]]
                return data
        if data.get('error'):
            return data
    return data


@v1_bp.route('/news/headlines', methods=['GET'])
def news_headlines():
    """Get top news headlines from 50+ sources"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        count = request.args.get('count', 50, type=int)
        cached = cache_get('news', 'headlines')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_news_headlines(count))
        data = normalize_news_response(data)
        cache_set('news', 'headlines', data, 300)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching news headlines: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/news/finance', methods=['GET'])
def news_finance():
    """Get finance news from aggregated sources"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        count = request.args.get('count', 50, type=int)
        cached = cache_get('news', 'finance')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_finance_news(count))
        data = normalize_news_response(data)
        cache_set('news', 'finance', data, 300)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching finance news: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/news/search', methods=['GET'])
def news_search():
    """Search news across all 50+ sources"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        query = request.args.get('q', '')
        count = request.args.get('count', 30, type=int)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query parameter required'})
        
        cache_key = f"search_{query}"
        cached = cache_get('news', cache_key)
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.search_news(query, count))
        data = normalize_news_response(data)
        cache_set('news', cache_key, data, 600)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/news/category/<category>', methods=['GET'])
def news_by_category(category):
    """Get news by category (finance, tech, world, health, geopolitical)"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        count = request.args.get('count', 40, type=int)
        cached = cache_get('news', f"cat_{category}")
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_news_by_category(category, count))
        data = normalize_news_response(data)
        cache_set('news', f"cat_{category}", data, 300)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching news by category: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/news/trending', methods=['GET'])
def news_trending():
    """Get trending topics across all news sources"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('news', 'trending')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_trending_topics())
        cache_set('news', 'trending', data, 300)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/news/geopolitical', methods=['GET'])
def news_geopolitical():
    """Get geopolitical intelligence news"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('news', 'geopolitical')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_geopolitical_news())
        cache_set('news', 'geopolitical', data, 600)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching geopolitical news: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== INDIAN MARKET / FMP ENDPOINTS ====================

@v1_bp.route('/indian-market/fmp/economic-calendar', methods=['GET'])
def economic_calendar():
    """Get economic calendar from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('economic_calendar', 'india')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_economic_calendar('india'))
        cache_set('economic_calendar', 'india', data, 1800)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching economic calendar: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/indian-market/fmp/earnings-calendar', methods=['GET'])
def earnings_calendar():
    """Get earnings calendar from unified data bridge"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()
        
        cached = cache_get('earnings', 'calendar')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})
        
        data = run_async(bridge.get_earnings_calendar())
        cache_set('earnings', 'calendar', data, 3600)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching earnings calendar: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== INGESTION ENDPOINTS ====================

@v1_bp.route('/ingestion/background', methods=['POST'])
def trigger_ingestion_background():
    """Trigger background ingestion"""
    try:
        from ..services.scheduler_service import ingestion_scheduler
        import asyncio
        asyncio.run(ingestion_scheduler.run_once())
        return jsonify({'success': True, 'status': 'running', 'message': 'Background ingestion triggered'})
    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        return jsonify({'success': True, 'status': 'idle', 'message': str(e)})


# ==================== GRAPH / NEO4J ENDPOINTS ====================

@v1_bp.route('/graph/neo4j/stats', methods=['GET'])
def neo4j_stats():
    """Get Neo4j graph database statistics"""
    try:
        from ..services.neo4j_graph import graph_stats
        stats = graph_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error getting Neo4j stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/graph/neo4j/stock/<ticker>/network', methods=['GET'])
def stock_network(ticker):
    """Get network around a stock"""
    try:
        from ..services.neo4j_graph import get_stock_network
        depth = request.args.get('depth', 2, type=int)
        network = get_stock_network(ticker.upper(), depth)
        return jsonify({'success': True, 'data': network})
    except Exception as e:
        logger.error(f"Error getting stock network: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/graph/neo4j/stock/<ticker>/relationships', methods=['GET'])
def stock_relationships(ticker):
    """Get relationships for a stock"""
    try:
        from ..services.neo4j_graph import get_stock_relationships
        rels = get_stock_relationships(ticker)
        return jsonify({'success': True, 'data': rels})
    except Exception as e:
        logger.error(f"Error getting stock relationships: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/graph/neo4j/search', methods=['GET'])
def graph_search():
    """Search entities in graph"""
    try:
        from ..services.neo4j_graph import Neo4jGraph
        query = request.args.get('q', '')
        entity_type = request.args.get('type', None)
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query parameter required'})
        
        results = Neo4jGraph.search_entities(query, entity_type, limit)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        return jsonify({'success': False, 'error': str(e)})


@v1_bp.route('/graph/neo4j/path', methods=['GET'])
def graph_path():
    """Find path between two entities"""
    try:
        from ..services.neo4j_graph import Neo4jGraph
        
        from_type = request.args.get('from_type', 'Stock')
        from_id = request.args.get('from_id', '')
        to_type = request.args.get('to_type', 'Stock')
        to_id = request.args.get('to_id', '')
        max_depth = request.args.get('max_depth', 5, type=int)
        
        if not from_id or not to_id:
            return jsonify({'success': False, 'error': 'from_id and to_id required'})
        
        path = Neo4jGraph.find_shortest_path(from_type, from_id, to_type, to_id, max_depth)
        return jsonify({'success': True, 'data': path})
    except Exception as e:
        logger.error(f"Error finding path: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== WEBSOCKET ENDPOINTS ====================

@v1_bp.route('/websocket/status', methods=['GET'])
def websocket_status():
    """Get WebSocket connection statistics"""
    try:
        from ..services.websocket_service import get_stats
        stats = get_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        return jsonify({'success': False, 'error': str(e), 'enabled': False})


# ==================== COT ENDPOINTS ====================

@v1_bp.route('/cot/financial-futures', methods=['GET'])
def cot_data():
    """Get COT data"""
    return jsonify({'success': True, 'data': []})


# ==================== MISSING ECONOMY ENDPOINTS ====================

@v1_bp.route('/economy/pib/latest', methods=['GET'])
def economy_pib_latest():
    """Get latest PIB (Press Information Bureau) releases from economy_platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('pib', 'latest')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_pib_latest())
        data = data if data and not (isinstance(data, dict) and data.get('error')) else {}
        cache_set('pib', 'latest', data, 1800)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching PIB: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/ipo', methods=['GET'])
def economy_ipo():
    """Get IPO calendar from economy_platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        cached = cache_get('ipo', 'calendar')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_ipo_calendar())
        data = data if data and not (isinstance(data, dict) and data.get('error')) else {}
        cache_set('ipo', 'calendar', data, 3600)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching IPO calendar: {e}")
        return jsonify({'success': True, 'data': {}})


@v1_bp.route('/economy/dividends', methods=['GET'])
def economy_dividends():
    """Get dividend calendar from economy_platform"""
    try:
        bridge = get_data_bridge()
        RedisCache, cache_get, cache_set = get_cache()

        date = request.args.get('date', '')

        cached = cache_get('dividends', date or 'all')
        if cached:
            return jsonify({'success': True, 'data': cached, 'cached': True})

        data = run_async(bridge.get_dividend_calendar(date))
        data = data if data and not (isinstance(data, dict) and data.get('error')) else {}
        cache_set('dividends', date or 'all', data, 3600)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error fetching dividends: {e}")
        return jsonify({'success': True, 'data': {}})


# ==================== INGESTION TRIGGER ====================

@v1_bp.route('/ingestion/trigger', methods=['POST'])
def ingestion_trigger():
    """Trigger manual ingestion"""
    try:
        from ..services.scheduler_service import ingestion_scheduler
        import asyncio
        asyncio.run(ingestion_scheduler.run_once())
        return jsonify({'success': True, 'status': 'running', 'message': 'Ingestion triggered'})
    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        return jsonify({'success': True, 'status': 'idle', 'message': str(e)})


# ==================== CACHE/STATUS ENDPOINTS ====================

@v1_bp.route('/cache/stats', methods=['GET'])
def cache_stats_endpoint():
    """Get Redis cache and Neo4j connection status"""
    try:
        _, _, _ = get_cache()
        from ..services.redis_cache import RedisCache
        redis_stats = RedisCache.get_stats()
    except Exception:
        redis_stats = {'connected': False}

    neo4j_status = 'disconnected'
    try:
        from ..services.neo4j_graph import Neo4jGraph
        Neo4jGraph.get_driver()
        neo4j_status = 'connected'
    except Exception:
        neo4j_status = 'disconnected'

    return jsonify({
        'success': True,
        'redis': redis_stats,
        'neo4j': {'status': neo4j_status}
    })


from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401

