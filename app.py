#!/usr/bin/env python3
"""
ERP Copilot Flask Application
Main entry point for the ERP Copilot system.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from erp_copilot.api.routes import app

if __name__ == "__main__":
    print("🚀 Starting ERP Copilot Flask Application...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: docs/API_DOCUMENTATION.md")
    print("⚙️  Configuration Guide: docs/ENDPOINTS_GUIDE.md")
    print()
    
    app.run(host="0.0.0.0", port=8000, debug=True)
