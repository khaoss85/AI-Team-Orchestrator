#!/usr/bin/env python3
"""
Test execution script
"""

import subprocess
import sys
import os

def run_test():
    """Run the E2E test"""
    print("🚀 RUNNING E2E TEST")
    print("=" * 30)
    
    # Set the working directory
    os.chdir('/Users/pelleri/Documents/ai-team-orchestrator/backend')
    
    try:
        # Try running the comprehensive test
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_comprehensive_e2e.py', 
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=600)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    sys.exit(0 if success else 1)