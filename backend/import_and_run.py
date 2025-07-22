#!/usr/bin/env python3
"""
Import and run test directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Now run the force test
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Try to run with subprocess
    try:
        result = subprocess.run([
            sys.executable, 
            'force_test_execution.py'
        ], 
        cwd='/Users/pelleri/Documents/ai-team-orchestrator/backend',
        capture_output=True, 
        text=True,
        timeout=120
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
    except Exception as e:
        print(f"Error running test: {e}")
        
        # Fallback: try direct import
        try:
            print("\nTrying direct import...")
            exec(open('/Users/pelleri/Documents/ai-team-orchestrator/backend/force_test_execution.py').read())
        except Exception as e2:
            print(f"Direct import failed: {e2}")