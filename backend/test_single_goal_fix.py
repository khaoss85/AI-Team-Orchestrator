#!/usr/bin/env python3
"""
Test single goal deliverable recreation with fixed JSON parsing
"""

import asyncio
from fix_deliverable_creation import force_create_goal_deliverable
from database import supabase

async def test_single_goal():
    """Test deliverable creation for the email sequence goal"""
    
    # Get the email sequence goal
    goal_id = '5c3beae6-9f0b-4c91-86c4-8d4902e1f879'
    goals_response = supabase.table('workspace_goals').select('*').eq('id', goal_id).execute()
    
    if not goals_response.data:
        print("Goal not found")
        return
    
    goal = goals_response.data[0]
    workspace_id = goal['workspace_id']
    
    print(f"Testing goal: {goal['description']}")
    
    # Delete existing deliverable for this goal
    deliverables_response = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    goal_deliverables = [d for d in deliverables_response.data if d.get('metadata', {}).get('goal_id') == goal_id]
    
    for d in goal_deliverables:
        supabase.table('deliverables').delete().eq('id', d['id']).execute()
        print(f"Deleted existing deliverable: {d['title']}")
    
    # Get related tasks
    tasks_response = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).execute()
    tasks = tasks_response.data
    
    print(f"Found {len(tasks)} total tasks")
    
    # Test deliverable creation
    try:
        deliverable_id = await force_create_goal_deliverable(workspace_id, goal, tasks)
        print(f"✅ Created deliverable: {deliverable_id}")
        
        # Check the content
        new_deliverable = supabase.table('deliverables').select('*').eq('id', deliverable_id).execute()
        if new_deliverable.data:
            content = new_deliverable.data[0].get('content', {})
            if isinstance(content, str):
                import json
                content = json.loads(content)
            
            concrete_deliverables = content.get('concrete_deliverables', [])
            print(f"\nContent analysis:")
            print(f"Total deliverables: {len(concrete_deliverables)}")
            
            for i, item in enumerate(concrete_deliverables):
                print(f"  {i+1}. Type: {item.get('type', 'unknown')}")
                print(f"      Name: {item.get('name', 'N/A')}")
                print(f"      Source: {item.get('source_key', 'N/A')}")
                
                # For email sequences, show email count
                if item.get('type') == 'email_sequence':
                    data = item.get('data', {})
                    if isinstance(data, dict) and 'emails' in data:
                        print(f"      Emails: {len(data['emails'])}")
                    elif isinstance(data, list):
                        print(f"      Items: {len(data)}")
    
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_single_goal())