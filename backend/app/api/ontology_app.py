"""
Ontology Flask App Integration for FastAPI
Mounts the Flask ontology application as a sub-application
"""

import os
import sys
from pathlib import Path

# Add the backend directory to path for imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the Flask app factory
from app.api.ontology import graph_bp, simulation_bp, report_bp
from flask import Flask
from app.config import settings

def create_ontology_flask_app():
    """Create and configure the Flask app for ontology"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.secret_key or 'aarambh-ontology-secret'
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    
    # Register blueprints
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'Aarambh Ontology'}
    
    return app

# Create the Flask app instance
ontology_flask_app = create_ontology_flask_app()
