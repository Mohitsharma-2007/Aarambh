"""
AARAMBH Ontology Backend Server — v1.0
=====================================
Dedicated server on port 8001 for the Ontology Engine.

Run:
  cd d:\\AARAMBH\\backend
  python ontology_server.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to path for imports
BASE_DIR = Path(__file__).parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.api.ontology_app import create_ontology_flask_app
from flask_cors import CORS

def main():
    print(f"\n{'='*65}")
    print("   AARAMBH — Ontology Engine Server v1.0")
    print("   Running on: http://localhost:8001")
    print(f"{'='*65}\n")
    
    app = create_ontology_flask_app()
    # Enable CORS for frontend
    CORS(app)
    
    app.run(host="0.0.0.0", port=8001, debug=True)

if __name__ == "__main__":
    main()
