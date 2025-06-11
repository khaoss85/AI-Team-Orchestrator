#!/usr/bin/env python3
"""Debug script to find specific tasks with contact lists and email sequences"""

import asyncio
import json
import logging
from database import list_tasks
from deliverable_system.concrete_asset_extractor import concrete_extractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_specific_tasks(workspace_id: str):
    """Find and debug specific tasks that should contain actionable assets"""
    
    logger.info(f"🔍 Debugging tasks in workspace: {workspace_id}")
    
    # Get all tasks
    tasks = await list_tasks(workspace_id)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    logger.info(f"Found {len(completed_tasks)} completed tasks")
    
    # Look for specific task patterns
    contact_tasks = []
    email_tasks = []
    
    for task in completed_tasks:
        task_name = task.get("name", "").lower()
        
        if "contact" in task_name and "research" in task_name:
            contact_tasks.append(task)
            logger.info(f"📞 Found contact task: {task.get('name')}")
            
        if "email" in task_name and ("sequence" in task_name or "strategy" in task_name):
            email_tasks.append(task)
            logger.info(f"📧 Found email task: {task.get('name')}")
    
    # Debug contact tasks
    logger.info(f"\n🎯 DEBUGGING {len(contact_tasks)} CONTACT TASKS:")
    for task in contact_tasks:
        await debug_task_details(task, "CONTACT")
    
    # Debug email tasks  
    logger.info(f"\n🎯 DEBUGGING {len(email_tasks)} EMAIL TASKS:")
    for task in email_tasks:
        await debug_task_details(task, "EMAIL")
    
    # Test extraction
    logger.info(f"\n🔬 TESTING CONCRETE EXTRACTION:")
    extracted_assets = await concrete_extractor.extract_concrete_assets(
        completed_tasks, "Marketing campaign", "business"
    )
    
    logger.info(f"Extracted {len(extracted_assets)} assets:")
    for asset_id, asset in extracted_assets.items():
        logger.info(f"  - {asset_id}: {asset.get('type')} (actionability: {asset.get('metadata', {}).get('business_actionability', 'N/A')})")

async def debug_task_details(task: dict, task_type: str):
    """Debug details of a specific task"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"{task_type} TASK ANALYSIS")
    logger.info(f"{'='*60}")
    logger.info(f"Task ID: {task.get('id')}")
    logger.info(f"Task Name: {task.get('name')}")
    logger.info(f"Status: {task.get('status')}")
    
    result = task.get("result", {})
    context_data = task.get("context_data", {}) or {}
    
    # Check result summary
    summary = result.get("summary", "")
    logger.info(f"Summary length: {len(summary)}")
    if summary:
        logger.info(f"Summary preview: {summary[:200]}...")
    
    # Check detailed_results_json
    detailed_json = result.get("detailed_results_json")
    if detailed_json:
        logger.info(f"✅ Has detailed_results_json")
        try:
            if isinstance(detailed_json, str):
                detailed_data = json.loads(detailed_json)
            else:
                detailed_data = detailed_json
            
            logger.info(f"Detailed data keys: {list(detailed_data.keys()) if isinstance(detailed_data, dict) else 'Not a dict'}")
            
            # Look for specific data
            if isinstance(detailed_data, dict):
                if "contacts" in detailed_data:
                    contacts = detailed_data["contacts"]
                    logger.info(f"🎯 FOUND CONTACTS: {len(contacts) if isinstance(contacts, list) else 'Not a list'}")
                    if isinstance(contacts, list) and len(contacts) > 0:
                        logger.info(f"First contact sample: {contacts[0] if contacts else 'None'}")
                
                if "email_sequences" in detailed_data:
                    sequences = detailed_data["email_sequences"]
                    logger.info(f"🎯 FOUND EMAIL SEQUENCES: {len(sequences) if isinstance(sequences, list) else 'Not a list'}")
                    if isinstance(sequences, list) and len(sequences) > 0:
                        logger.info(f"First sequence sample: {sequences[0] if sequences else 'None'}")
                
                # Look for other potential keys
                potential_keys = [k for k in detailed_data.keys() if any(word in k.lower() for word in ["contact", "email", "sequence", "list"])]
                if potential_keys:
                    logger.info(f"Other relevant keys: {potential_keys}")
            
        except Exception as e:
            logger.error(f"❌ Error parsing detailed_results_json: {e}")
    else:
        logger.info(f"❌ No detailed_results_json")
    
    # Check context_data
    if context_data:
        logger.info(f"Context data keys: {list(context_data.keys()) if isinstance(context_data, dict) else 'Not a dict'}")
        
        # Check precomputed deliverables
        if context_data.get("precomputed_deliverable", {}).get("actionable_assets"):
            assets = context_data["precomputed_deliverable"]["actionable_assets"]
            logger.info(f"🎯 FOUND PRECOMPUTED ASSETS: {list(assets.keys())}")
        
        if context_data.get("actionable_assets"):
            assets = context_data["actionable_assets"]
            logger.info(f"🎯 FOUND DIRECT ASSETS: {list(assets.keys())}")
    
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python debug_specific_tasks.py <workspace_id>")
        sys.exit(1)
    
    workspace_id = sys.argv[1]
    asyncio.run(debug_specific_tasks(workspace_id))