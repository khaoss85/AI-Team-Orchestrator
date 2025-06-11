#!/usr/bin/env python3
"""Test script to verify unified assets API fixes"""

import asyncio
import json
import logging
from routes.unified_assets import unified_asset_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_unified_assets_fix(workspace_id: str):
    """Test the unified assets API with the fixes"""
    
    logger.info(f"🧪 Testing unified assets API for workspace: {workspace_id}")
    
    try:
        # Call the unified asset manager directly
        result = await unified_asset_manager.get_workspace_assets(workspace_id)
        
        logger.info(f"✅ API call successful!")
        logger.info(f"Workspace ID: {result.get('workspace_id')}")
        logger.info(f"Asset count: {result.get('asset_count')}")
        logger.info(f"Data source: {result.get('data_source')}")
        
        assets = result.get('assets', {})
        logger.info(f"\n📦 ASSETS FOUND ({len(assets)}):")
        
        for asset_key, asset in assets.items():
            logger.info(f"\n  🎯 {asset_key}:")
            logger.info(f"    Name: {asset.get('name')}")
            logger.info(f"    Type: {asset.get('type')}")
            logger.info(f"    Ready to use: {asset.get('ready_to_use')}")
            logger.info(f"    Business actionability: {asset.get('business_actionability', 'N/A')}")
            logger.info(f"    Source task ID: {asset.get('sourceTaskId')}")
            
            # Show content preview
            content = asset.get('content', {})
            if content:
                logger.info(f"    Content enhancement: {content.get('enhancement_source', 'none')}")
                if content.get('structured_content'):
                    structured = content['structured_content']
                    logger.info(f"    Structured content keys: {list(structured.keys()) if isinstance(structured, dict) else 'not dict'}")
        
        # Analyze what we got
        contact_assets = [a for a in assets.values() if 'contact' in a.get('name', '').lower()]
        email_assets = [a for a in assets.values() if 'email' in a.get('name', '').lower()]
        
        logger.info(f"\n📊 ANALYSIS:")
        logger.info(f"  Contact-related assets: {len(contact_assets)}")
        logger.info(f"  Email-related assets: {len(email_assets)}")
        logger.info(f"  High actionability assets: {len([a for a in assets.values() if a.get('business_actionability', 0) > 0.8])}")
        
        if len(assets) == 1:
            logger.warning(f"⚠️  STILL ONLY 1 ASSET - May need deeper investigation")
        elif len(contact_assets) + len(email_assets) > 0:
            logger.info(f"🎉 SUCCESS - Found actionable assets!")
        else:
            logger.warning(f"⚠️  No contact/email assets found - Check task data")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error testing unified assets: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_unified_assets_fix.py <workspace_id>")
        sys.exit(1)
    
    workspace_id = sys.argv[1]
    result = asyncio.run(test_unified_assets_fix(workspace_id))