#!/usr/bin/env python3
"""
🚀 TEST DELIVERABLE VIA API
Test che crea deliverable usando l'API invece del database diretto
"""

import asyncio
import requests
import json
import time
import logging
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from database import list_tasks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

async def test_deliverable_via_api():
    """Test creazione deliverable via API"""
    
    logger.info("🚀 Testing Deliverable Creation via API")
    
    # Use the last successful workspace
    workspace_id = "4eaaaf40-150f-4d29-add0-6843db3070b4"
    
    try:
        # 1. Get completed tasks
        tasks = await list_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        logger.info(f"📊 Found {len(completed_tasks)} completed tasks")
        
        if not completed_tasks:
            logger.warning("⚠️ No completed tasks found")
            return False
        
        # 2. Create deliverable content from tasks
        task_summaries = []
        for i, task in enumerate(completed_tasks, 1):
            task_name = task.get("name", f"Task {i}")
            task_result = task.get("result", "No result")
            
            # Try to extract meaningful content
            try:
                if isinstance(task_result, str) and task_result.startswith('{'):
                    parsed = json.loads(task_result)
                    if "phases" in parsed:
                        phases = parsed["phases"]
                        phase_summary = f"- {len(phases)} phases defined"
                        task_summaries.append(f"**{task_name}**: {phase_summary}")
                    else:
                        task_summaries.append(f"**{task_name}**: Structured result with {len(parsed)} elements")
                else:
                    task_summaries.append(f"**{task_name}**: {str(task_result)[:100]}...")
            except:
                task_summaries.append(f"**{task_name}**: {str(task_result)[:100]}...")
        
        # 3. Create deliverable data
        deliverable_content = f"""# Project Deliverable

## Overview
This deliverable consolidates results from {len(completed_tasks)} completed task(s) in the AI Team Orchestrator project.

## Task Results
{chr(10).join(task_summaries)}

## Summary
The project team has successfully completed the initial phase of work, with concrete outputs and structured results ready for stakeholder review.

## Metrics
- Tasks completed: {len(completed_tasks)}
- Total result length: {sum(len(str(t.get('result', ''))) for t in completed_tasks)}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        deliverable_data = {
            "title": f"Project Progress Report - {len(completed_tasks)} Tasks",
            "type": "progress_report",
            "content": deliverable_content,
            "status": "completed",
            "readiness_score": 85,
            "completion_percentage": 100,
            "business_value_score": 80,
            "quality_metrics": {
                "task_count": len(completed_tasks),
                "content_length": len(deliverable_content),
                "source": "api_test"
            },
            "metadata": {
                "created_by": "test_script",
                "source_tasks": [t.get("id") for t in completed_tasks],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # 4. Create deliverable via API
        logger.info("📝 Creating deliverable via API...")
        
        response = requests.post(
            f"{API_BASE}/deliverables/workspace/{workspace_id}/create",
            json=deliverable_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            deliverable_id = result.get("deliverable", {}).get("id")
            
            logger.info(f"🎉 SUCCESS: Created deliverable {deliverable_id}")
            logger.info(f"   - Title: {deliverable_data['title']}")
            logger.info(f"   - Type: {deliverable_data['type']}")
            logger.info(f"   - Content length: {len(deliverable_content)}")
            
            # 5. Verify by fetching deliverables
            logger.info("🔍 Verifying deliverable creation...")
            
            fetch_response = requests.get(f"{API_BASE}/deliverables/workspace/{workspace_id}", timeout=10)
            
            if fetch_response.status_code == 200:
                deliverables = fetch_response.json()
                logger.info(f"✅ Verified: Found {len(deliverables)} deliverables")
                
                for i, deliverable in enumerate(deliverables, 1):
                    logger.info(f"  {i}. {deliverable.get('title')} - {deliverable.get('status')}")
                
                # Show sample content
                if deliverables:
                    sample_content = deliverables[0].get('content', '')[:200]
                    logger.info(f"📖 Sample content: {sample_content}...")
                
                return True
            else:
                logger.error(f"❌ Failed to verify deliverable: {fetch_response.status_code}")
                
        else:
            logger.error(f"❌ Failed to create deliverable: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Error in deliverable API test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    success = await test_deliverable_via_api()
    
    if success:
        logger.info("🎉 DELIVERABLE API TEST PASSED!")
        return 0
    else:
        logger.error("❌ DELIVERABLE API TEST FAILED!")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)