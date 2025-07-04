#!/usr/bin/env python3
"""
🚀 FORCE TASK GENERATION TEST
================================================================================
Test per forzare la generazione di task dal goal e verificare l'intero pipeline
"""

import asyncio
import requests
import time
import json
import sys
from datetime import datetime
from uuid import uuid4

async def force_task_generation():
    """Force task generation from goal"""
    base_url = "http://localhost:8000"
    
    print("🔧 FORCING TASK GENERATION FROM GOAL")
    print("=" * 60)
    
    # Create workspace and goal first
    workspace_data = {
        "name": "Force Task Test",
        "description": "Test for forcing task generation",
        "domain": "test"
    }
    
    print("📝 Creating workspace...")
    response = requests.post(f"{base_url}/workspaces", json=workspace_data, timeout=15)
    if response.status_code in [200, 201]:
        workspace = response.json()
        workspace_id = workspace.get('id')
        print(f"✅ Workspace: {workspace_id}")
    else:
        print(f"❌ Workspace failed: {response.status_code}")
        return False
    
    print("🎯 Creating goal...")
    goal_data = {
        "workspace_id": workspace_id,
        "metric_type": "deliverables",
        "target_value": 3.0,
        "unit": "components",
        "description": "Create 3 test components"
    }
    
    response = requests.post(f"{base_url}/api/workspaces/{workspace_id}/goals", json=goal_data, timeout=30)
    if response.status_code in [200, 201]:
        goal = response.json()
        goal_id = goal.get('id') or 'created'
        print(f"✅ Goal: {goal_id}")
    else:
        print(f"❌ Goal failed: {response.status_code}")
        return False
    
    # Create agents and approved proposal
    print("🤖 Creating team...")
    try:
        sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')
        from database import get_supabase_client
        supabase = get_supabase_client()
        
        # Create agents
        agents_data = [
            {'workspace_id': workspace_id, 'name': 'Test Lead', 'role': 'Project Manager', 'seniority': 'expert', 'status': 'available'},
            {'workspace_id': workspace_id, 'name': 'Dev 1', 'role': 'Backend Developer', 'seniority': 'senior', 'status': 'available'},
            {'workspace_id': workspace_id, 'name': 'Dev 2', 'role': 'Frontend Developer', 'seniority': 'senior', 'status': 'available'}
        ]
        
        for agent in agents_data:
            result = supabase.table('agents').insert(agent).execute()
            if result.data:
                print(f"   ✅ Created: {agent['name']}")
        
        # Create approved proposal
        proposal_data = {
            "workspace_id": workspace_id,
            "proposal_data": {
                "agents": [{"name": agent["name"], "role": agent["role"]} for agent in agents_data],
                "rationale": "Test team for task generation"
            },
            "status": "approved",
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table('team_proposals').insert(proposal_data).execute()
        if result.data:
            proposal_id = result.data[0]['id']
            print(f"   ✅ Approved proposal: {proposal_id}")
        
    except Exception as e:
        print(f"❌ Team creation error: {e}")
        return False
    
    # Force goal-driven task generation
    print("\n🚀 Forcing goal-driven task generation...")
    try:
        from goal_driven_task_planner import goal_driven_task_planner
        
        # Get the actual goal ID from database
        goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', workspace_id).execute()
        if goals_response.data:
            goal_data = goals_response.data[0]
            actual_goal_id = goal_data['id']
            print(f"   📋 Found goal ID: {actual_goal_id}")
            
            # Force task generation using the correct method
            print("   ⚡ Calling goal_driven_task_planner.plan_tasks_for_goal...")
            tasks = await goal_driven_task_planner.plan_tasks_for_goal(goal_data, workspace_id)
            
            if tasks:
                print(f"   🎉 SUCCESS! Generated {len(tasks)} tasks!")
                for i, task in enumerate(tasks[:5]):
                    print(f"      {i+1}. {task.get('name', 'Unnamed')}")
            else:
                print("   ⚠️ No tasks generated")
        else:
            print("   ❌ Could not find goal in database")
            
    except Exception as e:
        print(f"   ❌ Goal-driven task generation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check final task count
    print("\n📊 Final verification...")
    try:
        response = requests.get(f"{base_url}/workspaces/{workspace_id}/tasks", timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Total tasks in workspace: {len(tasks)}")
            if len(tasks) > 0:
                print("🎉 AUTONOMOUS TASK GENERATION SUCCESSFUL!")
                return True
        else:
            print(f"⚠️ Task check failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Task verification error: {e}")
    
    # Cleanup
    try:
        requests.delete(f"{base_url}/workspaces/{workspace_id}", timeout=10)
    except:
        pass
    
    return False

if __name__ == "__main__":
    success = asyncio.run(force_task_generation())
    print(f"\n{'🎉 SUCCESS!' if success else '❌ FAILED'}")
    exit(0 if success else 1)