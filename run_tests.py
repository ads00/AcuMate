#!/usr/bin/env python3
"""
Quick test runner for the ERP Copilot system.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_flask_app import main

if __name__ == "__main__":
    print("🧪 Running ERP Copilot Test Suite...")
    print("=" * 60)
    main()
