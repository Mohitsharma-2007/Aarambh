"""
Aarambh Backend - Flask Application Factory
"""

import os
import warnings

# Suppress multiprocessing resource_tracker warnings (from third-party libraries like transformers)
# Must be set before all other imports
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask Application Factory Function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set JSON encoding: ensure Chinese characters display directly (not as \uXXXX format)
    # Flask >= 2.3 uses app.json.ensure_ascii, older versions use JSON_AS_ASCII config
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Setup logger
    logger = setup_logger('aarambh')
    
    # Only print startup message in reloader subprocess (avoid printing twice in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Aarambh Backend Starting...")
        logger.info("=" * 50)
    
    # Enable CORS for all routes (fix Axios errors)
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
            "supports_credentials": True
        }
    })
    
    # Register simulation process cleanup function (ensure all simulation processes terminate when server shuts down)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation process cleanup function registered")
    
    # Import all blueprints FIRST (before defining routes)
    from .api import graph_bp, simulation_bp, report_bp, v1_bp
    
    # DEBUG: Log v1 routes
    logger.info(f"V1 blueprint routes: {len(v1_bp.deferred_functions)}")
    
    # Register blueprints
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(v1_bp, url_prefix='/api/v1')
    
    # DEBUG: Log all routes after registration
    all_routes = [str(r.rule) for r in app.url_map.iter_rules() if '/api/v1' in str(r.rule)]
    logger.info(f"Registered v1 routes: {len(all_routes)}")
    for route in all_routes[:10]:
        logger.info(f"  {route}")
    
    # Root URL - Debug Dashboard
    @app.route('/')
    def root_dashboard():
        """API Debug Dashboard"""
        routes = sorted([str(r.rule) for r in app.url_map.iter_rules() 
                        if not str(r.rule).startswith('/static') and '<' not in str(r.rule)])
        
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Aarambh Backend API Debug</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 40px; background: #f5f5f5; }
        h1 { color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f0f4ff; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card h3 { margin: 0; font-size: 2em; color: #4a5568; }
        .stat-card p { margin: 5px 0 0; color: #718096; }
        .routes { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .route-group { background: #f7fafc; padding: 15px; border-radius: 8px; }
        .route-group h3 { margin-top: 0; color: #2d3748; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        .route-group ul { list-style: none; padding: 0; margin: 0; }
        .route-group li { padding: 5px 0; border-bottom: 1px solid #edf2f7; font-family: monospace; font-size: 13px; }
        .route-group li:last-child { border-bottom: none; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .badge-get { background: #c6f6d5; color: #22543d; }
        .badge-post { background: #bee3f8; color: #2a4365; }
        .badge-green { background: #c6f6d5; color: #22543d; }
        .status-ok { color: #38a169; }
        .links { margin: 20px 0; }
        .links a { display: inline-block; margin-right: 15px; padding: 10px 20px; background: #4299e1; color: white; text-decoration: none; border-radius: 5px; }
        .links a:hover { background: #3182ce; }
        .test-section { margin-top: 30px; padding: 20px; background: #fffaf0; border-radius: 8px; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 4px; font-family: monospace; }
        .test-pass { background: #c6f6d5; }
        .test-fail { background: #fed7d7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Aarambh Backend API Debug Dashboard</h1>
        <p>Base URL: <code>http://127.0.0.1:5001</code></p>
        
        <div class="links">
            <a href="/docs">📚 API Docs</a>
            <a href="/health">🏥 Health Check</a>
            <a href="/api/v1/market/heatmap">📊 Test Market API</a>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>''' + str(len(routes)) + '''</h3>
                <p>Total API Routes</p>
            </div>
            <div class="stat-card">
                <h3 class="status-ok">●</h3>
                <p>Server Status</p>
            </div>
        </div>
        
        <div class="routes">
            <div class="route-group">
                <h3>🔐 Auth</h3>
                <ul>
                    <li><span class="badge badge-post">POST</span> /api/v1/auth/login</li>
                    <li><span class="badge badge-post">POST</span> /api/v1/auth/register</li>
                    <li><span class="badge badge-get">GET</span> /api/v1/auth/me</li>
                </ul>
            </div>
            <div class="route-group">
                <h3>📡 Graph/Ontology</h3>
                <ul>
                    <li><span class="badge badge-post">POST</span> /api/graph/build</li>
                    <li><span class="badge badge-post">POST</span> /api/graph/ontology/generate</li>
                    <li><span class="badge badge-get">GET</span> /api/graph/project/list</li>
                    <li><span class="badge badge-get">GET</span> /api/graph/data/&lt;id&gt;</li>
                </ul>
            </div>
            <div class="route-group">
                <h3>📊 Market</h3>
                <ul>
                    <li><span class="badge badge-get">GET</span> /api/v1/market/heatmap</li>
                    <li><span class="badge badge-get">GET</span> /api/v1/market/indices</li>
                    <li><span class="badge badge-get">GET</span> /api/v1/market/crypto</li>
                    <li><span class="badge badge-get">GET</span> /api/v1/economy/overview</li>
                </ul>
            </div>
            <div class="route-group">
                <h3>🤖 AI</h3>
                <ul>
                    <li><span class="badge badge-post">POST</span> /api/v1/ai/chat</li>
                    <li><span class="badge badge-get">GET</span> /api/v1/ai/providers</li>
                    <li><span class="badge badge-post">POST</span> /api/v1/kg/research</li>
                </ul>
            </div>
        </div>
        
        <div class="test-section">
            <h3>🔧 Quick Test URLs</h3>
            <p>Click to test APIs in browser:</p>
            <ul>
                <li><a href="/api/v1/auth/me" target="_blank">Test Auth → /api/v1/auth/me</a></li>
                <li><a href="/api/v1/events/" target="_blank">Test Events → /api/v1/events/</a></li>
                <li><a href="/api/v1/analytics/overview" target="_blank">Test Analytics → /api/v1/analytics/overview</a></li>
            </ul>
        </div>
    </div>
</body>
</html>'''
        return html
    
    # API Documentation page
    @app.route('/docs')
    def api_docs():
        """API Documentation"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Aarambh API Documentation</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 0; background: #f5f5f5; }
        .header { background: #2d3748; color: white; padding: 20px 40px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px; }
        .endpoint { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .method { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-right: 10px; }
        .method-GET { background: #c6f6d5; color: #22543d; }
        .method-POST { background: #bee3f8; color: #2a4365; }
        .path { font-family: monospace; font-size: 16px; color: #2d3748; }
        .desc { color: #718096; margin-top: 10px; }
        .section { margin: 40px 0; }
        .section h2 { color: #2d3748; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        code { background: #edf2f7; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Aarambh API Documentation</h1>
        <p>Base URL: <code>http://127.0.0.1:5001</code> | <a href="/" style="color: #90cdf4;">← Back to Dashboard</a></p>
    </div>
    <div class="container">
        <div class="section">
            <h2>Getting Started</h2>
            <p>All API endpoints return JSON responses. For authenticated endpoints, include the token in the Authorization header:</p>
            <code>Authorization: Bearer YOUR_TOKEN</code>
        </div>
        
        <div class="section">
            <h2>🔐 Authentication</h2>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/v1/auth/login</span>
                <p class="desc">Login with email and password. Returns access token.</p>
            </div>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/v1/auth/register</span>
                <p class="desc">Register a new user account.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/auth/me</span>
                <p class="desc">Get current user profile.</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📡 Graph & Ontology</h2>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/graph/ontology/generate</span>
                <p class="desc">Generate ontology from uploaded documents.</p>
            </div>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/graph/build</span>
                <p class="desc">Build knowledge graph from ontology.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/graph/data/{graph_id}</span>
                <p class="desc">Get graph nodes and edges.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/graph/project/{project_id}/state</span>
                <p class="desc">Get project state and redirect URL.</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Market Data</h2>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/market/heatmap</span>
                <p class="desc">Get market heatmap data (all stocks).</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/market/quote/{ticker}</span>
                <p class="desc">Get stock quote by ticker symbol.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/market/indices</span>
                <p class="desc">Get major market indices.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/economy/overview</span>
                <p class="desc">Get economy overview with macro indicators.</p>
            </div>
        </div>
        
        <div class="section">
            <h2>🤖 AI & Research</h2>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/v1/ai/chat</span>
                <p class="desc">Send message to AI chat.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/v1/ai/providers</span>
                <p class="desc">Get available AI providers and models.</p>
            </div>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/v1/kg/research</span>
                <p class="desc">Run ontology research query.</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Simulation</h2>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/simulation/create</span>
                <p class="desc">Create new simulation.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/simulation/list</span>
                <p class="desc">List all simulations.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/simulation/{id}</span>
                <p class="desc">Get simulation details.</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📄 Reports</h2>
            <div class="endpoint">
                <span class="method method-POST">POST</span>
                <span class="path">/api/report/generate</span>
                <p class="desc">Generate report from simulation.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/report/list</span>
                <p class="desc">List all reports.</p>
            </div>
            <div class="endpoint">
                <span class="method method-GET">GET</span>
                <span class="path">/api/report/{id}</span>
                <p class="desc">Get report details.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        return html
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'Aarambh Backend'}
    
    # Report viewing endpoint - serves full_report.md for direct browser viewing
    @app.route('/interaction/<report_id>')
    def view_report(report_id):
        """Serve report markdown file for direct viewing"""
        import os
        from flask import send_from_directory, abort
        
        report_path = os.path.join(Config.UPLOAD_FOLDER, 'reports', report_id)
        report_file = os.path.join(report_path, 'full_report.md')
        
        if not os.path.exists(report_file):
            abort(404, description=f"Report not found: {report_id}")
        
        return send_from_directory(report_path, 'full_report.md', mimetype='text/markdown')
    
    if should_log_startup:
        logger.info("Aarambh Backend Startup Complete")
    
    return app
