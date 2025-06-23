#!/usr/bin/env python3
"""
🔧 DEBUG: Goal to Task Generation
Test rapido per identificare perché i goal non generano task
"""

import asyncio
import sys
import os
import logging
from uuid import uuid4

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_goal_to_task_generation():
    """Test rapido della catena Goal → Task"""
    logger.info("🔧 DEBUG: Goal to Task Generation")
    
    try:
        from database import create_workspace, supabase
        
        # Step 1: Create simple workspace
        workspace_data = {
            "name": "Debug Test Workspace",
            "description": "Simple test for goal-task chain",
            "user_id": str(uuid4()),
            "goal": "Creare un database di 50 contatti B2B per marketing"
        }
        
        workspace = await create_workspace(**workspace_data)
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Workspace created: {workspace_id}")
        
        # Step 2: Create manual goal (bypass AI extraction for debug)
        manual_goal = {
            "workspace_id": workspace_id,
            "metric_type": "contacts",
            "target_value": 50.0,
            "unit": "contacts",
            "description": "Create B2B contact database with 50 qualified leads",
            "priority": 3,
            "status": "active"
        }
        
        goal_response = supabase.table('workspace_goals').insert(manual_goal).execute()
        if not goal_response.data:
            raise Exception("Failed to create manual goal")
        
        created_goal = goal_response.data[0]
        logger.info(f"✅ Manual goal created: {created_goal['id']}")
        logger.info(f"   Description: {created_goal['description']}")
        logger.info(f"   Metric Type: {created_goal['metric_type']}")
        logger.info(f"   Target: {created_goal['target_value']} {created_goal['unit']}")
        
        # Step 3: Test task generation
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        
        planner = GoalDrivenTaskPlanner()
        logger.info("✅ GoalDrivenTaskPlanner initialized")
        
        logger.info(f"🎯 Generating tasks for goal: {created_goal['description'][:50]}...")
        
        try:
            # Convert dict to WorkspaceGoal object for the planner
            from models import WorkspaceGoal
            from uuid import UUID
            
            from datetime import datetime
            
            goal_obj = WorkspaceGoal(
                id=UUID(created_goal['id']),
                workspace_id=UUID(created_goal['workspace_id']),
                metric_type=created_goal['metric_type'],
                target_value=created_goal['target_value'],
                current_value=created_goal.get('current_value', 0.0),
                unit=created_goal['unit'],
                description=created_goal['description'],
                priority=created_goal['priority'],
                status=created_goal['status'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"   Goal remaining value: {goal_obj.remaining_value}")
            
            tasks = await planner._generate_tasks_for_goal(goal_obj)
            logger.info(f"✅ Generated {len(tasks)} tasks")
            
            for i, task in enumerate(tasks):
                logger.info(f"   Task {i+1}: {task.get('name', 'Unnamed')}")
                logger.info(f"     Description: {task.get('description', 'No description')[:100]}")
                logger.info(f"     Role: {task.get('assigned_to_role', 'Unassigned')}")
                logger.info(f"     Priority: {task.get('priority', 'Unknown')}")
            
            if len(tasks) > 0:
                logger.info("🎉 SUCCESS: Goal-to-Task generation working!")
                return True
            else:
                logger.error("❌ ISSUE: No tasks generated")
                return False
                
        except Exception as task_error:
            logger.error(f"❌ Task generation failed: {task_error}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the debug test"""
    logger.info("🚀 STARTING GOAL-TO-TASK DEBUG TEST")
    
    success = await test_goal_to_task_generation()
    
    if success:
        logger.info("🎉 DEBUG TEST PASSED - Goal-to-Task generation working!")
    else:
        logger.error("💥 DEBUG TEST FAILED - Issue in goal-to-task chain")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)