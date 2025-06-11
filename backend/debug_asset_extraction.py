#!/usr/bin/env python3
"""Debug script to analyze asset extraction from database"""

import asyncio
import json
import logging
from database import list_tasks, get_workspace
from deliverable_system.concrete_asset_extractor import concrete_extractor
from routes.unified_assets import unified_asset_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_asset_extraction():
    """Debug asset extraction to see why we're only getting 1 generic asset"""
    
    # Test workspace ID (replace with actual)
    workspace_id = "YOUR_WORKSPACE_ID"  # Replace this with actual workspace ID
    
    # 1. Get all completed tasks
    tasks = await list_tasks(workspace_id)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    logger.info(f"\n🔍 Found {len(completed_tasks)} completed tasks")
    
    # 2. Analyze each task for assets
    logger.info("\n📋 ANALYZING EACH TASK:")
    logger.info("=" * 80)
    
    for task in completed_tasks:
        task_name = task.get("name", "")
        result = task.get("result", {})
        context_data = task.get("context_data", {}) or {}
        
        logger.info(f"\n📌 Task: {task_name}")
        logger.info(f"   ID: {task.get('id')}")
        logger.info(f"   Status: {task.get('status')}")
        
        # Check for dual output format
        if result.get("detailed_results_json"):
            try:
                detailed = result["detailed_results_json"]
                if isinstance(detailed, str):
                    detailed = json.loads(detailed)
                
                logger.info(f"   ✅ Has detailed_results_json")
                
                # Check for structured content
                if detailed.get("structured_content"):
                    logger.info(f"   ✅ Has structured_content in dual format")
                    logger.info(f"      Keys: {list(detailed['structured_content'].keys())[:5]}")
                
                # Check for specific asset types
                if "contacts" in str(detailed).lower():
                    logger.info(f"   🎯 CONTAINS CONTACTS DATA")
                    
                if "email_sequences" in str(detailed).lower() or "sequences" in str(detailed).lower():
                    logger.info(f"   🎯 CONTAINS EMAIL SEQUENCES")
                    
                # Show first 200 chars of detailed results
                detailed_str = json.dumps(detailed) if isinstance(detailed, dict) else str(detailed)
                logger.info(f"   Preview: {detailed_str[:200]}...")
                
            except Exception as e:
                logger.error(f"   ❌ Error parsing detailed_results_json: {e}")
        
        # Check context data
        if context_data.get("precomputed_deliverable", {}).get("actionable_assets"):
            logger.info(f"   ✅ Has precomputed actionable_assets")
            assets = context_data["precomputed_deliverable"]["actionable_assets"]
            logger.info(f"      Asset keys: {list(assets.keys())}")
        
        if context_data.get("actionable_assets"):
            logger.info(f"   ✅ Has direct actionable_assets")
            assets = context_data["actionable_assets"]
            logger.info(f"      Asset keys: {list(assets.keys())}")
    
    # 3. Test concrete asset extraction
    logger.info("\n\n🔬 TESTING CONCRETE ASSET EXTRACTION:")
    logger.info("=" * 80)
    
    workspace = await get_workspace(workspace_id)
    workspace_goal = workspace.get("goal", "") if workspace else ""
    
    extracted_assets = await concrete_extractor.extract_concrete_assets(
        completed_tasks, workspace_goal, "business"
    )
    
    logger.info(f"\n📊 Extracted {len(extracted_assets)} concrete assets:")
    for asset_id, asset in extracted_assets.items():
        logger.info(f"\n   🎯 {asset_id}:")
        logger.info(f"      Type: {asset.get('type')}")
        logger.info(f"      Source: {asset.get('source')}")
        logger.info(f"      Source Task: {asset.get('metadata', {}).get('source_task')}")
        logger.info(f"      Actionability: {asset.get('metadata', {}).get('business_actionability', 'N/A')}")
        logger.info(f"      Ready to use: {asset.get('metadata', {}).get('ready_to_use')}")
    
    # 4. Test unified asset manager
    logger.info("\n\n🔧 TESTING UNIFIED ASSET MANAGER:")
    logger.info("=" * 80)
    
    unified_result = await unified_asset_manager.get_workspace_assets(workspace_id)
    
    logger.info(f"\n📦 Unified API returned {unified_result.get('asset_count')} assets:")
    for asset_key, asset in unified_result.get("assets", {}).items():
        logger.info(f"\n   📄 {asset_key}:")
        logger.info(f"      Name: {asset.get('name')}")
        logger.info(f"      Type: {asset.get('type')}")
        logger.info(f"      Versions: {asset.get('versions')}")
        logger.info(f"      Ready to use: {asset.get('ready_to_use')}")

if __name__ == "__main__":
    # Get workspace ID from command line or use default
    import sys
    workspace_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not workspace_id:
        print("Usage: python debug_asset_extraction.py <workspace_id>")
        print("\nPlease provide a workspace ID to debug")
        sys.exit(1)
    
    # Update the workspace ID in the function
    import inspect
    import types
    
    # Create a new function with the workspace_id bound
    original_func = debug_asset_extraction
    code = original_func.__code__
    new_code = code.replace(
        co_consts=tuple(
            workspace_id if const == "YOUR_WORKSPACE_ID" else const
            for const in code.co_consts
        )
    )
    new_func = types.FunctionType(
        new_code,
        original_func.__globals__,
        original_func.__name__,
        original_func.__defaults__,
        original_func.__closure__
    )
    
    # Run the debug function
    asyncio.run(new_func())