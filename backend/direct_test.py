#!/usr/bin/env python3
"""
Direct test execution
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Set working directory
backend_path = Path('/Users/pelleri/Documents/ai-team-orchestrator/backend')
os.chdir(backend_path)

def run_test():
    """Run the E2E test using subprocess"""
    print("🚀 RUNNING E2E TEST")
    print("=" * 30)
    
    try:
        # Use subprocess to run pytest
        cmd = [sys.executable, '-m', 'pytest', 'tests/test_comprehensive_e2e.py::test_run_full_autonomous_flow', '-v', '-s']
        
        print(f"Executing: {' '.join(cmd)}")
        print(f"Working directory: {os.getcwd()}")
        
        result = subprocess.run(cmd, 
                              capture_output=False, 
                              text=True, 
                              cwd=backend_path)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}")
    sys.exit(0 if success else 1)