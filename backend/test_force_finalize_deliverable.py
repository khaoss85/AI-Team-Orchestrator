#!/usr/bin/env python3
"""
🚀 TEST FORCE FINALIZE DELIVERABLE
Test che usa l'endpoint force-finalize per creare deliverable
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_force_finalize_deliverable():
    """Test force finalize deliverable endpoint"""
    
    logger.info("🚀 Testing Force Finalize Deliverable")
    
    # Use the last successful workspace
    workspace_id = "4eaaaf40-150f-4d29-add0-6843db3070b4"
    
    try:
        # 1. Check current deliverables
        logger.info("📊 Checking current deliverables...")
        
        initial_response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}", timeout=10)
        
        if initial_response.status_code == 200:
            initial_deliverables = initial_response.json()
            logger.info(f"   - Initial deliverables: {len(initial_deliverables)}")
        else:
            logger.warning(f"   - Could not fetch initial deliverables: {initial_response.status_code}")
            initial_deliverables = []
        
        # 2. Force finalize deliverables
        logger.info("🚀 Calling force-finalize endpoint...")
        
        response = requests.post(
            f"{API_BASE}/deliverables/workspace/{workspace_id}/force-finalize",
            timeout=60  # Longer timeout for processing
        )
        
        if response.status_code == 200:
            result = response.json()
            
            logger.info(f"✅ Force finalize successful!")
            logger.info(f"   - Success: {result.get('success')}")
            logger.info(f"   - Count: {result.get('count')}")
            logger.info(f"   - Message: {result.get('message')}")
            
            # Show deliverables
            deliverables = result.get('deliverables', [])
            
            if deliverables:
                logger.info(f"📦 Created deliverables:")
                for i, deliverable in enumerate(deliverables, 1):
                    logger.info(f"  {i}. {deliverable.get('title', 'Unknown')}")
                    logger.info(f"     - ID: {deliverable.get('id')}")
                    logger.info(f"     - Type: {deliverable.get('type')}")
                    logger.info(f"     - Status: {deliverable.get('status')}")
                    logger.info(f"     - Content length: {len(deliverable.get('content', ''))}")
                
                # Show sample content from first deliverable
                if deliverables:
                    sample_content = deliverables[0].get('content', '')
                    logger.info(f"📖 Sample content (first 300 chars):")
                    logger.info(f"   {sample_content[:300]}...")
                
                return True
            else:
                logger.warning("⚠️ No deliverables were created")
                return False
                
        else:
            logger.error(f"❌ Force finalize failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in force finalize test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    success = await test_force_finalize_deliverable()
    
    if success:
        logger.info("🎉 FORCE FINALIZE DELIVERABLE TEST PASSED!")
        return 0
    else:
        logger.error("❌ FORCE FINALIZE DELIVERABLE TEST FAILED!")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)