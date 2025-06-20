#!/usr/bin/env python3
"""
Test Backend Startup
"""

import sys
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

print("Testing backend imports...")

try:
    from main import app
    print("✅ Main app imported successfully")
    
    # Check if documents router is included
    router_names = [route.path for route in app.routes]
    if any('/documents' in path for path in router_names):
        print("✅ Documents router is registered")
    else:
        print("❌ Documents router not found in app routes")
        
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()