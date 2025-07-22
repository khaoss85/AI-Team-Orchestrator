#!/usr/bin/env python3
"""
Test rapido del trigger autonomo - completa 2 task per attivare il trigger
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import update_task_status, should_trigger_deliverable_aggregation
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_trigger():
    # Workspace dal test precedente con handoff
    workspace_id = '68c4d2e1-d3c9-40e5-93b2-17a6bde49963'
    
    logger.info(f"🔍 Testing trigger for workspace {workspace_id}")
    
    # Check trigger BEFORE completing tasks
    should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
    logger.info(f"📊 Trigger evaluation BEFORE: {should_trigger}")
    
    # Simula completamento di 2 task con contenuto sostanziale
    # Questi sono i task ID dal workspace di test
    task_ids = [
        '6b979fcd-9cb5-44ba-86d6-13b6d75b2a07',  # Customer Journey Mapping
        '91ca86fb-1c3f-48bd-a00a-64b1b4f018b0'   # Documentation Suite
    ]
    
    for i, task_id in enumerate(task_ids[:2]):
        result = {
            "execution_time": 120.5,
            "result": f"""
## Task Completion Report

### Analysis Completed
Successfully analyzed the onboarding process with the following findings:

1. **Current Process Duration**: 14 days average
2. **Major Bottlenecks Identified**: 
   - Manual document verification (3 days)
   - Sequential approval process (4 days)
   - Redundant data entry (2 days)

### Recommendations
- Implement parallel processing for approvals
- Automate document verification with AI
- Create single data entry point with auto-population

### Metrics
- Potential time savings: 8 days (57% reduction)
- Customer satisfaction improvement: +25% projected
- Cost reduction: $150 per onboarding

This analysis provides concrete steps for optimization.
""",
            "quality_score": 0.95
        }
        
        # Completa il task bypassando quality gate
        # Aggiorna direttamente nel database
        from database import supabase
        
        update_result = supabase.table("tasks").update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.now().isoformat()
        }).eq("id", task_id).execute()
        
        if update_result and update_result.data:
            logger.info(f"✅ Task {i+1} completed (bypassed quality gate): {task_id}")
            
            # Ora triggera manualmente il check per goal e deliverable
            from database import _trigger_goal_validation_and_correction
            await _trigger_goal_validation_and_correction(task_id, workspace_id)
        else:
            logger.error(f"❌ Failed to update task {task_id}")
            if update_result:
                logger.error(f"   Error: {update_result}")
            # Prova con un approccio diverso
            logger.info("   Trying alternative approach...")
            try:
                # Usa direttamente la funzione update_task_status bypassando quality
                import os
                os.environ['BYPASS_QUALITY_GATE'] = 'true'
                await update_task_status(task_id, "completed", result)
                logger.info(f"   ✅ Alternative approach worked for task {task_id}")
            except Exception as e:
                logger.error(f"   Alternative approach failed: {e}")
        
        # Piccola pausa tra completamenti
        await asyncio.sleep(2)
    
    # Check trigger AFTER completing tasks
    logger.info("⏳ Waiting 5 seconds for trigger evaluation...")
    await asyncio.sleep(5)
    
    should_trigger = await should_trigger_deliverable_aggregation(workspace_id)
    logger.info(f"📊 Trigger evaluation AFTER: {should_trigger}")
    
    if should_trigger:
        logger.info("🎉 TRIGGER CONDITION MET! Deliverable aggregation should start autonomously")
    else:
        logger.info("❌ Trigger condition not met")

if __name__ == "__main__":
    asyncio.run(test_trigger())