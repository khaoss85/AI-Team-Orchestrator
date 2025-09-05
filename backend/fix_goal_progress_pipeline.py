#!/usr/bin/env python3
"""
Manual fix script to unblock goals by generating tasks and assigning agents
"""
import os
import sys
import asyncio
from datetime import datetime
from uuid import uuid4
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

workspace_id = "f79d87cc-b61f-491d-9226-4220e39e71ad"

async def fix_goal_progress_pipeline():
    """Main function to fix goal progress pipeline"""
    
    print("\n" + "="*80)
    print("🔧 GOAL PROGRESS PIPELINE FIX SCRIPT")
    print("="*80)
    print(f"Workspace ID: {workspace_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)
    
    # Step 1: Get all goals for workspace
    print("\n📊 Step 1: Fetching workspace goals...")
    goals_result = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id).execute()
    
    if not goals_result.data:
        print("❌ No goals found for workspace!")
        return
    
    goals = goals_result.data
    print(f"✅ Found {len(goals)} goals")
    
    # Step 2: Get all existing tasks
    print("\n📝 Step 2: Fetching existing tasks...")
    tasks_result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
    tasks = tasks_result.data if tasks_result.data else []
    print(f"✅ Found {len(tasks)} existing tasks")
    
    # Step 3: Get available agents
    print("\n🤖 Step 3: Fetching available agents...")
    agents_result = supabase.table("agents").select("*").eq("workspace_id", workspace_id).execute()
    agents = agents_result.data if agents_result.data else []
    print(f"✅ Found {len(agents)} agents")
    
    if not agents:
        print("❌ No agents available! Cannot proceed without agents.")
        return
    
    # Step 4: Analyze and fix each goal
    print("\n🔍 Step 4: Analyzing and fixing goals...")
    
    goals_needing_tasks = []
    tasks_needing_agents = []
    
    for goal in goals:
        goal_id = goal['id']
        goal_desc = goal.get('description', goal_id)[:50]
        
        # Check if goal has tasks (check goal_id field)
        goal_tasks = [t for t in tasks if t.get('goal_id') == goal_id]
        
        if not goal_tasks:
            goals_needing_tasks.append(goal)
            print(f"\n⚠️ Goal needs tasks: {goal_desc}")
        else:
            print(f"\n✅ Goal has {len(goal_tasks)} tasks: {goal_desc}")
            
            # Check if tasks have agents
            for task in goal_tasks:
                if not task.get('agent_id'):
                    tasks_needing_agents.append(task)
                    print(f"   ⚠️ Task needs agent: {task.get('name', task.get('title', task['id'][:8]))}")
    
    # Step 5: Generate tasks for goals without tasks
    if goals_needing_tasks:
        print(f"\n🔧 Step 5: Generating tasks for {len(goals_needing_tasks)} goals...")
        
        for goal in goals_needing_tasks:
            await generate_tasks_for_goal(goal, agents, workspace_id)
    else:
        print("\n✅ Step 5: All goals have tasks")
    
    # Step 6: Assign agents to tasks without agents
    if tasks_needing_agents:
        print(f"\n🔧 Step 6: Assigning agents to {len(tasks_needing_agents)} tasks...")
        
        agent_index = 0
        for task in tasks_needing_agents:
            # Round-robin agent assignment
            agent = agents[agent_index % len(agents)]
            agent_index += 1
            
            # Update task with agent assignment
            update_result = supabase.table("tasks").update({
                "agent_id": agent['id'],
                "status": "pending",  # Ensure it's ready to be picked up
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", task['id']).execute()
            
            if update_result.data:
                print(f"   ✅ Assigned {agent.get('role', 'agent')} to task: {task.get('name', task.get('title', task['id'][:8]))}")
            else:
                print(f"   ❌ Failed to assign agent to task: {task['id'][:8]}")
    else:
        print("\n✅ Step 6: All tasks have agents assigned")
    
    # Step 7: Trigger task execution for pending tasks
    print("\n🚀 Step 7: Checking task execution status...")
    
    # Re-fetch tasks to get updated data
    tasks_result = supabase.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
    tasks = tasks_result.data if tasks_result.data else []
    
    pending_tasks = [t for t in tasks if t.get('status') == 'pending']
    if pending_tasks:
        print(f"   ⚠️ {len(pending_tasks)} tasks are pending and should be picked up by the executor")
        print("   💡 The task executor should automatically pick these up in the next cycle")
    
    in_progress_tasks = [t for t in tasks if t.get('status') == 'in_progress']
    if in_progress_tasks:
        print(f"   🔄 {len(in_progress_tasks)} tasks are currently in progress")
    
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    if completed_tasks:
        print(f"   ✅ {len(completed_tasks)} tasks have been completed")
    
    failed_tasks = [t for t in tasks if t.get('status') in ['failed', 'needs_revision']]
    if failed_tasks:
        print(f"   ❌ {len(failed_tasks)} tasks have failed and may need intervention")
    
    # Step 8: Update goal progress based on completed tasks
    print("\n📊 Step 8: Updating goal progress...")
    
    for goal in goals:
        goal_id = goal['id']
        goal_tasks = [t for t in tasks if t.get('goal_id') == goal_id]
        
        if goal_tasks:
            completed_count = len([t for t in goal_tasks if t.get('status') == 'completed'])
            total_count = len(goal_tasks)
            
            if total_count > 0:
                # Update goal progress
                progress_percentage = min((completed_count / total_count) * 100, 100.0)  # Cap at 100%
                
                update_data = {
                    "current_value": float(completed_count),
                    "assets_completed_count": completed_count,
                    "asset_requirements_count": total_count,
                    "asset_completion_rate": round(progress_percentage, 2),  # Round to 2 decimal places
                    "last_progress_update": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # If goal type is deliverable and we have progress, update it
                if goal.get('goal_type') == 'deliverable' and goal.get('target_value', 0) == 1:
                    update_data['current_value'] = 1 if progress_percentage >= 100 else 0
                
                update_result = supabase.table("workspace_goals").update(update_data).eq("id", goal_id).execute()
                
                if update_result.data:
                    print(f"   ✅ Updated goal progress: {goal.get('description', goal_id)[:30]}... ({progress_percentage:.0f}%)")
                else:
                    print(f"   ❌ Failed to update goal: {goal_id[:8]}")
    
    print("\n" + "="*80)
    print("🎯 FIX COMPLETE - SUMMARY")
    print("="*80)
    print(f"✅ Goals processed: {len(goals)}")
    print(f"✅ Tasks generated for: {len(goals_needing_tasks)} goals")
    print(f"✅ Agents assigned to: {len(tasks_needing_agents)} tasks")
    print(f"✅ Progress updated for all goals with tasks")
    print("\n💡 NEXT STEPS:")
    print("1. The task executor should pick up pending tasks automatically")
    print("2. Monitor the backend logs to see task execution")
    print("3. Check the frontend to see updated progress")
    print("="*80)


async def generate_tasks_for_goal(goal, agents, workspace_id):
    """Generate tasks for a goal that has no tasks"""
    
    goal_desc = goal.get('description', '')
    goal_type = goal.get('goal_type', 'deliverable')
    
    # Define task templates based on goal type
    task_templates = []
    
    if 'email' in goal_desc.lower() or 'sequence' in goal_desc.lower():
        # Email sequence tasks
        task_templates = [
            {
                "title": f"Draft email content for {goal_desc[:30]}",
                "description": f"Create compelling email content for the goal: {goal_desc}",
                "priority": "high"
            },
            {
                "title": f"Review and refine email sequence",
                "description": f"Review the drafted email for quality, tone, and effectiveness",
                "priority": "medium"
            },
            {
                "title": f"Prepare implementation instructions",
                "description": f"Create step-by-step instructions for implementing the email sequence",
                "priority": "medium"
            }
        ]
    elif 'contatti' in goal_desc.lower() or 'contact' in goal_desc.lower() or 'list' in goal_desc.lower():
        # Contact list tasks
        task_templates = [
            {
                "title": f"Research and identify contacts",
                "description": f"Research and compile a list of qualified contacts for: {goal_desc}",
                "priority": "high"
            },
            {
                "title": f"Validate and enrich contact data",
                "description": f"Validate contact information and add LinkedIn profiles and company details",
                "priority": "medium"
            },
            {
                "title": f"Format and prepare final deliverable",
                "description": f"Format the contact list as a CSV file with all required fields",
                "priority": "low"
            }
        ]
    elif 'istruzioni' in goal_desc.lower() or 'instruction' in goal_desc.lower() or 'setup' in goal_desc.lower():
        # Setup instructions tasks
        task_templates = [
            {
                "title": f"Create setup documentation",
                "description": f"Write comprehensive setup instructions for: {goal_desc}",
                "priority": "high"
            },
            {
                "title": f"Add screenshots and examples",
                "description": f"Enhance documentation with visual aids and practical examples",
                "priority": "medium"
            }
        ]
    else:
        # Generic tasks for any goal
        task_templates = [
            {
                "title": f"Analyze requirements for {goal_desc[:30]}",
                "description": f"Analyze and break down the requirements for: {goal_desc}",
                "priority": "high"
            },
            {
                "title": f"Execute main deliverable",
                "description": f"Create the main deliverable for: {goal_desc}",
                "priority": "high"
            },
            {
                "title": f"Quality assurance and finalization",
                "description": f"Review and finalize the deliverable for: {goal_desc}",
                "priority": "medium"
            }
        ]
    
    # Create tasks in database
    created_count = 0
    agent_index = 0
    
    for task_template in task_templates:
        # Assign agent (round-robin)
        agent = agents[agent_index % len(agents)]
        agent_index += 1
        
        # Create task
        task_data = {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "goal_id": goal['id'],  # Link to goal using goal_id 
            "name": task_template['title'],  # Use 'name' instead of 'title'
            "description": task_template['description'],
            "status": "pending",
            "priority": task_template['priority'],
            "agent_id": agent['id'],  # Use 'agent_id' instead of 'assigned_agent_id'
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "context_data": {  # Use 'context_data' instead of 'metadata'
                "auto_generated": True,
                "generated_by": "fix_goal_progress_pipeline",
                "goal_type": goal_type,
                "assigned_agent_role": agent.get('role', 'unknown')
            }
        }
        
        try:
            result = supabase.table("tasks").insert(task_data).execute()
            if result.data:
                created_count += 1
                print(f"   ✅ Created task: {task_template['title'][:50]}...")
        except Exception as e:
            print(f"   ❌ Failed to create task: {e}")
    
    print(f"   📊 Created {created_count}/{len(task_templates)} tasks for goal")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(fix_goal_progress_pipeline())