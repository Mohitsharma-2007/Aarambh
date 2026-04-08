"""
AARAMBH Backend - Simple Start Script
"""
import os
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print(f"\n{'='*60}")
    print("AARAMBH Backend Starting...")
    print(f"API Base: http://127.0.0.1:5001")
    print(f"{'='*60}\n")
    
    # Run without reloader to ensure all routes are registered
    app.run(
        host='0.0.0.0', 
        port=5001, 
        debug=False, 
        threaded=True,
        use_reloader=False
    )
