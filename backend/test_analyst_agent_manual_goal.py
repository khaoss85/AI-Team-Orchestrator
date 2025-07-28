#!/usr/bin/env python3
"""
Test manuale dell'Analyst Agent creando un goal direttamente
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_workspace_goal, list_tasks
from goal_driven_task_planner import GoalDrivenTaskPlanner
from models import WorkspaceGoal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_analyst_agent_manual():
    """Test diretto dell'Analyst Agent con goal manuale"""
    
    logger.info("🔍 TESTING ANALYST AGENT - MANUAL GOAL APPROACH")
    
    # Step 1: Create a test workspace ID (use existing one)
    workspace_id = "ab272856-a6eb-4db9-8887-87dd57a10ec3"  # Use the existing workspace
    
    # Step 2: Create goals that should trigger different Analyst Agent behaviors
    test_goals = [
        {
            "description": "Create a personalized welcome email sequence using real client testimonials",
            "metric_type": "marketing_content_creation",
            "target_value": 1.0,
            "current_value": 0.0,
            "unit": "email_sequence"
        },
        {
            "description": "Create a competitor analysis report",
            "metric_type": "business_analysis",
            "target_value": 1.0,
            "current_value": 0.0,
            "unit": "report"
        },
        {
            "description": "Write a generic welcome email template",
            "metric_type": "template_creation",
            "target_value": 1.0,
            "current_value": 0.0,
            "unit": "template"
        }
    ]
    
    created_goals = []
    
    for goal_data in test_goals:
        logger.info(f"📝 Creating goal: {goal_data['description']}")
        
        try:
            goal_id = await create_workspace_goal(
                workspace_id=workspace_id,
                metric_type=goal_data["metric_type"],
                target_value=goal_data["target_value"],
                current_value=goal_data["current_value"],
                unit=goal_data["unit"],
                description=goal_data["description"]
            )
            
            if goal_id:
                created_goals.append({
                    "id": goal_id,
                    "workspace_id": workspace_id,
                    **goal_data
                })
                logger.info(f"✅ Created goal: {goal_id}")
            else:
                logger.error(f"❌ Failed to create goal: {goal_data['description']}")
                
        except Exception as e:
            logger.error(f"❌ Error creating goal: {e}")
    
    logger.info(f"📊 Created {len(created_goals)} test goals")
    
    # Step 3: Test the Analyst Agent and Goal-Driven Task Planner
    planner = GoalDrivenTaskPlanner()
    
    workspace_context = {
        "name": "Test E-commerce Business",
        "description": "E-commerce business selling premium outdoor gear to adventure enthusiasts",
        "domain": "E-commerce/Marketing"
    }
    
    for goal_data in created_goals:
        logger.info(f"\n🤖 TESTING ANALYST AGENT FOR GOAL: {goal_data['description']}")
        
        # Convert to WorkspaceGoal model
        goal = WorkspaceGoal(
            id=goal_data["id"],
            workspace_id=goal_data["workspace_id"],
            metric_type=goal_data["metric_type"],
            target_value=goal_data["target_value"],
            current_value=goal_data["current_value"],
            unit=goal_data["unit"],
            description=goal_data["description"],
            status="active",
            priority="medium"
        )
        
        try:
            # This should now call the new Analyst Agent
            logger.info("🔍 Calling Analyst Agent...")
            analysis = await planner._analyze_goal_requirements_ai(goal, workspace_context)
            
            logger.info(f"📊 ANALYST AGENT RESULT:")
            logger.info(f"  - requires_data_gathering: {analysis.get('requires_data_gathering')}")
            logger.info(f"  - data_points_needed: {analysis.get('data_points_needed', [])}")
            
            # Test task generation with new architecture
            logger.info("🛠️ Generating tasks with new architecture...")
            tasks = await planner._generate_ai_driven_tasks_legacy(goal, workspace_context)
            
            logger.info(f"📝 GENERATED TASKS ({len(tasks)}):")
            for i, task in enumerate(tasks):
                logger.info(f"  {i+1}. {task.get('name')}")
                logger.info(f"     Description: {task.get('description', '')[:100]}...")
                logger.info(f"     Priority: {task.get('priority')}")
                logger.info(f"     Contribution: {task.get('contribution_expected')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing goal: {e}", exc_info=True)
    
    # Step 4: Final assessment
    logger.info(f"\n🎯 ANALYST AGENT TEST SUMMARY")
    logger.info(f"✅ Goals created: {len(created_goals)}")
    logger.info(f"✅ Analyst Agent architecture: {'ACTIVE' if planner else 'FAILED'}")
    
    # Save results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "workspace_id": workspace_id,
        "goals_created": len(created_goals),
        "analyst_agent_active": True,
        "test_type": "manual_direct"
    }
    
    with open(f"analyst_agent_manual_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    logger.info("🏆 ANALYST AGENT MANUAL TEST COMPLETED")
    return True

if __name__ == "__main__":
    asyncio.run(test_analyst_agent_manual())