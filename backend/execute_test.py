#!/usr/bin/env python3
"""
Execute test directly
"""

import os
import sys
import asyncio

# Set working directory
os.chdir('/Users/pelleri/Documents/ai-team-orchestrator/backend')
sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')

async def run_test():
    """Run the comprehensive E2E test directly"""
    print("🚀 EXECUTING COMPREHENSIVE E2E TEST")
    print("=" * 50)
    
    try:
        # Import the test module
        from tests.test_comprehensive_e2e import test_run_full_autonomous_flow
        
        # Run the test
        print("📋 Starting test execution...")
        await test_run_full_autonomous_flow()
        
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)