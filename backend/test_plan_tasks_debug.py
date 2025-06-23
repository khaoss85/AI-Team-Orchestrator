#!/usr/bin/env python3
"""
🔧 DEBUG: plan_tasks_for_goal specifically
Test the plan_tasks_for_goal method that creates tasks with agent assignment
"""

import asyncio
import sys
import os
import logging
from uuid import uuid4
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_plan_tasks_for_goal():
    """Test plan_tasks_for_goal method specifically"""
    logger.info("🔧 DEBUG: plan_tasks_for_goal method")
    
    try:
        from database import create_workspace, supabase
        
        # Step 1: Create simple workspace
        workspace_data = {
            "name": "Plan Tasks Debug Workspace",
            "description": "Testing plan_tasks_for_goal method",
            "user_id": str(uuid4()),
            "goal": "Test goal for debugging task planning"
        }
        
        workspace = await create_workspace(**workspace_data)
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Workspace created: {workspace_id}")
        
        # Step 2: Create manual goal
        manual_goal = {
            "workspace_id": workspace_id,
            "metric_type": "contacts",
            "target_value": 25.0,
            "unit": "contacts",
            "description": "Create B2B contact database with 25 qualified leads",
            "priority": 3,
            "status": "active"
        }
        
        goal_response = supabase.table('workspace_goals').insert(manual_goal).execute()
        if not goal_response.data:
            raise Exception("Failed to create manual goal")
        
        created_goal = goal_response.data[0]
        logger.info(f"✅ Manual goal created: {created_goal['id']}")
        
        # Step 3: Create agents for task assignment
        simple_agents = [
            {
                "workspace_id": workspace_id,
                "name": "Contact Research Specialist",
                "role": "contact_researcher",
                "seniority": "senior",
                "description": "Specialist in B2B contact research",
                "status": "available",
                "health": {"status": "healthy"},
                "system_prompt": "You are a contact research specialist.",
                "tools": [],
                "can_create_tools": False
            },
            {
                "workspace_id": workspace_id,
                "name": "Lead Generation Expert", 
                "role": "lead_generator",
                "seniority": "expert",
                "description": "Expert in lead generation and qualification",
                "status": "available",
                "health": {"status": "healthy"},
                "system_prompt": "You are a lead generation expert.",
                "tools": [],
                "can_create_tools": False
            }
        ]
        
        created_agents = []
        for agent_data in simple_agents:
            agent_response = supabase.table('agents').insert(agent_data).execute()
            if agent_response.data:
                created_agents.append(agent_response.data[0])
        
        logger.info(f"✅ Agents created: {len(created_agents)}")
        
        # Step 4: Test plan_tasks_for_goal method
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        
        planner = GoalDrivenTaskPlanner()
        logger.info("✅ GoalDrivenTaskPlanner initialized")
        
        # Prepare goal dict for plan_tasks_for_goal
        goal_dict = {
            'id': created_goal['id'],
            'workspace_id': created_goal['workspace_id'],
            'metric_type': created_goal['metric_type'],
            'target_value': created_goal['target_value'],
            'current_value': created_goal.get('current_value', 0.0),
            'unit': created_goal['unit'],
            'description': created_goal['description'],
            'priority': created_goal['priority'],
            'status': created_goal['status'],
            'created_at': created_goal.get('created_at') or datetime.now().isoformat(),
            'updated_at': created_goal.get('updated_at') or datetime.now().isoformat()
        }
        
        logger.info(f"🎯 Calling plan_tasks_for_goal for goal: {created_goal['description'][:50]}...")
        logger.info(f"   Available agents: {len(created_agents)}")
        logger.info(f"   Goal dict keys: {list(goal_dict.keys())}")
        
        try:
            tasks = await planner.plan_tasks_for_goal(goal_dict, workspace_id)
            logger.info(f"✅ plan_tasks_for_goal succeeded! Created {len(tasks)} tasks")
            
            for i, task in enumerate(tasks):
                logger.info(f"   Task {i+1}: {task.get('name', 'Unnamed')}")
                logger.info(f"     ID: {task.get('id', 'No ID')}")
                logger.info(f"     Agent ID: {task.get('agent_id', 'No agent_id')}")
                logger.info(f"     Status: {task.get('status', 'No status')}")
            
            # Verify tasks were actually created in database
            tasks_check = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
            db_tasks = tasks_check.data or []
            logger.info(f"✅ Verified: {len(db_tasks)} tasks found in database")
            
            if len(tasks) > 0 and len(db_tasks) > 0:
                logger.info("🎉 SUCCESS: plan_tasks_for_goal working correctly!")
                return True
            else:
                logger.error("❌ ISSUE: plan_tasks_for_goal returned tasks but none in database")
                return False
                
        except Exception as plan_error:
            logger.error(f"❌ plan_tasks_for_goal failed: {plan_error}")
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
    logger.info("🚀 STARTING PLAN-TASKS-FOR-GOAL DEBUG TEST")
    
    success = await test_plan_tasks_for_goal()
    
    if success:
        logger.info("🎉 DEBUG TEST PASSED - plan_tasks_for_goal working!")
    else:
        logger.error("💥 DEBUG TEST FAILED - Issue in plan_tasks_for_goal")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)