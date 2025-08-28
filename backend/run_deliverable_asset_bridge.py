#!/usr/bin/env python3
"""
🔗 Deliverable to Asset Artifact Bridge Runner

This script processes existing deliverables that don't have corresponding asset_artifacts,
fixing the broken pipeline between deliverables and frontend display.

Based on db-steward findings: 6 deliverables exist but 0 asset_artifacts
"""

import asyncio
import logging
from database import batch_convert_existing_deliverables_to_assets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the deliverable to asset artifact conversion"""
    print("🔗 Starting Deliverable → Asset Artifact Bridge")
    print("=" * 60)
    
    # Target workspace with the 6 deliverables (correct ID from db check)
    workspace_id = "5975922e-c943-4d99-ad1d-25c01a81da7d"
    
    try:
        # Run batch conversion for the specific workspace
        logger.info(f"🎯 Processing workspace: {workspace_id}")
        results = await batch_convert_existing_deliverables_to_assets(
            workspace_id=workspace_id,
            limit=20  # Safety limit
        )
        
        # Display results
        print("\n📊 CONVERSION RESULTS:")
        print("-" * 40)
        print(f"📦 Total deliverables found: {results['total_deliverables_found']}")
        print(f"🔄 Processed: {results['processed_count']}")
        print(f"✅ Successful: {results['successful_count']}")
        print(f"⏭️ Skipped (already converted): {results['skipped_count']}")
        print(f"❌ Failed: {results['failed_count']}")
        print(f"📈 Success rate: {results['success_rate']:.1f}%")
        
        if results['errors']:
            print(f"\n⚠️ ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   - {error}")
        
        print("\n🎯 NEXT STEPS:")
        if results['successful_count'] > 0:
            print("   1. ✅ Check frontend deliverables tab - should show readable content")
            print("   2. ✅ New deliverables will automatically create asset_artifacts")
            print("   3. ✅ Pipeline is now complete: deliverables → asset_artifacts → frontend")
        else:
            print("   1. ⚠️ No deliverables were converted - check logs for issues")
            print("   2. ⚠️ Verify deliverables exist in database")
            print("   3. ⚠️ Check if asset_artifacts already exist")
            
    except Exception as e:
        logger.error(f"❌ Error in main conversion process: {e}")
        print(f"\n❌ FATAL ERROR: {e}")
        return False
    
    return results['successful_count'] > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
    print(f"\n🏁 Bridge process completed with exit code: {exit_code}")
    exit(exit_code)