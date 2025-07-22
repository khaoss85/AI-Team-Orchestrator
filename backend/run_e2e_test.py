#!/usr/bin/env python3
"""
Script per eseguire il test E2E completo
"""

import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Run the test directly
if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE E2E TEST")
    print("=" * 50)
    
    try:
        # Import and run the test
        from comprehensive_e2e_test import ComprehensiveE2ETestSuite
        
        async def main():
            print("📋 Initializing test suite...")
            test_suite = ComprehensiveE2ETestSuite()
            
            print("▶️  Running full test suite...")
            result = await test_suite.run_full_test_suite()
            
            print("\n🎯 TEST RESULTS:")
            print("=" * 30)
            print(f"Overall Result: {'✅ PASSED' if result.get('overall_success') else '❌ FAILED'}")
            print(f"Compliance: {result.get('compliance_percentage', 0):.1f}%")
            print(f"Pillars Tested: {result.get('total_pillars_tested', 0)}")
            print(f"Pillars Passed: {result.get('pillars_passed', 0)}")
            
            if result.get('detailed_results'):
                print("\n📊 DETAILED RESULTS:")
                for pillar, status in result['detailed_results'].items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {status_icon} {pillar}")
            
            return result.get('overall_success', False)
        
        # Run the test
        success = asyncio.run(main())
        
        if success:
            print("\n🎉 E2E TEST COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ E2E TEST FAILED!")
            
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ ERROR RUNNING TEST: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)