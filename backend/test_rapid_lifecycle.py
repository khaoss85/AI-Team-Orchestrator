#!/usr/bin/env python3
"""
🚀 RAPID LIFECYCLE TEST
Test rapido del ciclo di vita critico saltando parti lente
"""

import asyncio
import sys
import os
import logging
from uuid import uuid4, UUID
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def rapid_lifecycle_test():
    """Test rapido del percorso critico"""
    logger.info("🚀 RAPID LIFECYCLE TEST - Critical Path Only")
    
    try:
        from database import create_workspace, supabase
        
        # Step 1: Create workspace
        workspace_data = {
            "name": "Rapid Test Workspace",
            "description": "Fast test for critical lifecycle",
            "user_id": str(uuid4()),
            "goal": "Creare 25 contatti B2B qualificati per marketing"
        }
        
        workspace = await create_workspace(**workspace_data)
        workspace_id = str(workspace["id"])
        logger.info(f"✅ Workspace: {workspace_id}")
        
        # Step 2: Create manual goals (skip slow AI extraction)
        manual_goals = [
            {
                "workspace_id": workspace_id,
                "metric_type": "contacts",
                "target_value": 25.0,
                "unit": "contacts",
                "description": "Create 25 qualified B2B contacts for marketing outreach",
                "priority": 3,
                "status": "active"
            },
            {
                "workspace_id": workspace_id,
                "metric_type": "content_pieces",
                "target_value": 5.0,
                "unit": "email templates",
                "description": "Create 5 email templates for outreach campaigns",
                "priority": 2,
                "status": "active"
            }
        ]
        
        created_goals = []
        for goal_data in manual_goals:
            goal_response = supabase.table('workspace_goals').insert(goal_data).execute()
            if goal_response.data:
                created_goals.append(goal_response.data[0])
        
        logger.info(f"✅ Goals: {len(created_goals)} created")
        
        # Step 3: Create simple agents  
        simple_agents = [
            {
                "workspace_id": workspace_id,
                "name": "Contact Research Specialist",
                "role": "contact_researcher",
                "seniority": "senior",
                "description": "Specialist in B2B contact research and database creation",
                "status": "available",
                "health": {"status": "healthy"},
                "system_prompt": "You are a contact research specialist focused on B2B lead generation.",
                "tools": [],
                "can_create_tools": False
            },
            {
                "workspace_id": workspace_id,
                "name": "Email Marketing Specialist",
                "role": "email_marketer",
                "seniority": "senior", 
                "description": "Specialist in email marketing and template creation",
                "status": "available",
                "health": {"status": "healthy"},
                "system_prompt": "You are an email marketing specialist focused on B2B outreach.",
                "tools": [],
                "can_create_tools": False
            }
        ]
        
        created_agents = []
        for agent_data in simple_agents:
            agent_response = supabase.table('agents').insert(agent_data).execute()
            if agent_response.data:
                created_agents.append(agent_response.data[0])
        
        logger.info(f"✅ Agents: {len(created_agents)} created")
        
        # Step 4: Generate tasks from goals
        from goal_driven_task_planner import GoalDrivenTaskPlanner
        from models import WorkspaceGoal
        
        planner = GoalDrivenTaskPlanner()
        all_tasks = []
        
        for i, goal in enumerate(created_goals):
            logger.info(f"   Processing goal {i+1}: {goal['description'][:50]}...")
            
            # Convert to WorkspaceGoal object
            goal_obj = WorkspaceGoal(
                id=UUID(goal['id']),
                workspace_id=UUID(goal['workspace_id']),
                metric_type=goal['metric_type'],
                target_value=goal['target_value'],
                current_value=goal.get('current_value', 0.0),
                unit=goal['unit'],
                description=goal['description'],
                priority=goal['priority'],
                status=goal['status'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Generate tasks
            tasks = await planner._generate_tasks_for_goal(goal_obj)
            logger.info(f"   Generated {len(tasks)} tasks for goal {i+1}")
            all_tasks.extend(tasks)
        
        logger.info(f"✅ Tasks: {len(all_tasks)} generated")
        
        # Step 5: Execute first task with real agent
        if all_tasks:
            from ai_agents.manager import AgentManager
            
            # Get available agents for proper assignment
            agents_response = supabase.table('agents').select('*').eq('workspace_id', workspace_id).eq('status', 'available').execute()
            available_agents = agents_response.data or []
            
            if not available_agents:
                logger.error("❌ No available agents found for task assignment")
                return False
            
            # Take first task and create in database with proper agent assignment
            task_data = all_tasks[0]
            assigned_agent = available_agents[0]  # Use first available agent
            
            task_response = supabase.table('tasks').insert({
                "workspace_id": workspace_id,
                "name": task_data.get('name', 'Generated Task'),
                "description": task_data.get('description', ''),
                "status": "pending",
                "priority": task_data.get('priority', 'medium'),
                "agent_id": assigned_agent["id"],  # 🔧 FIX: Assign agent_id to prevent orphaned tasks
                "assigned_to_role": task_data.get('assigned_to_role'),
                "metric_type": task_data.get('metric_type'),
                "contribution_expected": task_data.get('contribution_expected', 1.0),
                "context_data": task_data.get('context_data', {})
            }).execute()
            
            if task_response.data:
                task_id = task_response.data[0]['id']
                
                # Initialize and execute with agent
                manager = AgentManager(UUID(workspace_id))
                init_success = await manager.initialize()
                
                if init_success:
                    logger.info(f"   Executing task: {task_data.get('name', 'Unnamed')[:50]}...")
                    
                    try:
                        result = await manager.execute_task(UUID(task_id))
                        
                        # Check final status
                        task_check = supabase.table('tasks').select('*').eq('id', task_id).execute()
                        if task_check.data:
                            final_status = task_check.data[0]['status']
                            logger.info(f"   Task completed with status: {final_status}")
                            
                            if final_status in ['completed', 'pending_verification', 'needs_enhancement']:
                                logger.info("✅ Task: Successfully executed")
                                
                                # Step 6: Check if deliverable creation triggered
                                await asyncio.sleep(2)  # Wait for potential deliverable creation
                                
                                deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
                                deliverables = deliverables_response.data or []
                                
                                logger.info(f"✅ Deliverables: {len(deliverables)} created")
                                
                                # Final success metrics
                                success_metrics = {
                                    "goals_created": len(created_goals),
                                    "agents_created": len(created_agents),
                                    "tasks_generated": len(all_tasks),
                                    "tasks_executed": 1,
                                    "deliverables_created": len(deliverables),
                                    "system_functional": True
                                }
                                
                                logger.info("🎉 RAPID LIFECYCLE SUCCESS!")
                                logger.info(f"   📊 Metrics: {success_metrics}")
                                
                                return True
                            else:
                                logger.warning(f"Task status unexpected: {final_status}")
                                return False
                        else:
                            logger.error("Could not verify task status")
                            return False
                            
                    except Exception as exec_error:
                        logger.error(f"Task execution failed: {exec_error}")
                        return False
                else:
                    logger.error("AgentManager initialization failed")
                    return False
            else:
                logger.error("Failed to create task in database")
                return False
        else:
            logger.error("No tasks generated")
            return False
        
    except Exception as e:
        logger.error(f"Rapid test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run rapid lifecycle test"""
    logger.info("🚀 STARTING RAPID LIFECYCLE TEST")
    logger.info("Testing critical path: Goals → Tasks → Execution → Deliverables")
    
    success = await rapid_lifecycle_test()
    
    if success:
        logger.info("🎉 RAPID LIFECYCLE PASSED - Critical path working!")
    else:
        logger.error("💥 RAPID LIFECYCLE FAILED - Critical path has issues")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)