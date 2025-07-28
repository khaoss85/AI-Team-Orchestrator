#!/usr/bin/env python3
"""
Analyze the complete workflow pattern to understand the delegation issue
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def analyze_workflow_pattern():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"Analyzing complete workflow pattern for workspace: {workspace_id}")
    print("=" * 80)
    
    # 1. Check goals for this workspace
    print("1. GOALS:")
    print("-" * 20)
    goals_result = supabase.table('goals').select('*').eq('workspace_id', workspace_id).execute()
    goals = goals_result.data
    
    print(f"Found {len(goals)} goals")
    for i, goal in enumerate(goals, 1):
        print(f"{i}. Goal: {goal.get('description', 'No description')}")
        print(f"   Status: {goal.get('status', 'Unknown')}")
        print(f"   Created: {goal.get('created_at', 'Unknown')}")
        print()
    
    # 2. Check agents
    print("2. AGENTS:")
    print("-" * 20)
    agents_result = supabase.table('agents').select('*').eq('workspace_id', workspace_id).execute()
    agents = agents_result.data
    
    print(f"Found {len(agents)} agents")
    for i, agent in enumerate(agents, 1):
        print(f"{i}. Agent: {agent.get('name', 'No name')}")
        print(f"   Role: {agent.get('role', 'Unknown')}")
        print(f"   Seniority: {agent.get('seniority_level', 'Unknown')}")
        print(f"   Status: {agent.get('status', 'Unknown')}")
        print()
    
    # 3. Check task creation pattern - when were tasks created?
    print("3. TASK CREATION TIMELINE:")
    print("-" * 20)
    
    tasks_result = supabase.table('tasks').select('id, name, created_at, agent_id, result').eq('workspace_id', workspace_id).order('created_at').execute()
    tasks = tasks_result.data
    
    print("Task created timeline (showing first 10):")
    for i, task in enumerate(tasks[:10], 1):
        print(f"{i}. {task['created_at']}: {task['name'][:50]}...")
        
        # Check if this task created sub-tasks
        result = task.get('result', {})
        if isinstance(result, dict) and 'defined_sub_tasks' in result:
            print(f"   └─ Created {len(result['defined_sub_tasks'])} sub-tasks")
        elif isinstance(result, dict) and 'structured_content' in result:
            try:
                structured = json.loads(result['structured_content']) if isinstance(result['structured_content'], str) else result['structured_content']
                if isinstance(structured, dict) and 'assets' in structured:
                    print(f"   └─ Created {len(structured['assets'])} assets")
                else:
                    print(f"   └─ Has structured content (no assets)")
            except:
                print(f"   └─ Has structured content (unparseable)")
        elif result:
            print(f"   └─ Has result content")
        else:
            print(f"   └─ No result")
    
    # 4. Analysis of the pattern
    print("\n4. PATTERN ANALYSIS:")
    print("-" * 20)
    
    # Count task types
    asset_creation_tasks = [t for t in tasks if t['name'].startswith('Create Asset:')]
    other_tasks = [t for t in tasks if not t['name'].startswith('Create Asset:')]
    
    print(f"Asset creation tasks: {len(asset_creation_tasks)}")
    print(f"Other tasks: {len(other_tasks)}")
    
    # Check if tasks are creating sub-tasks vs producing content
    tasks_creating_subtasks = 0
    tasks_creating_assets = 0
    tasks_with_content = 0
    
    for task in tasks:
        result = task.get('result', {})
        if isinstance(result, dict):
            if 'defined_sub_tasks' in result and result['defined_sub_tasks']:
                tasks_creating_subtasks += 1
            elif 'structured_content' in result:
                try:
                    structured = json.loads(result['structured_content']) if isinstance(result['structured_content'], str) else result['structured_content']
                    if isinstance(structured, dict) and 'assets' in structured and structured['assets']:
                        tasks_creating_assets += 1
                    else:
                        tasks_with_content += 1
                except:
                    tasks_with_content += 1
            elif result:
                tasks_with_content += 1
    
    print(f"\nTask output analysis:")
    print(f"- Tasks creating sub-tasks: {tasks_creating_subtasks}")
    print(f"- Tasks creating assets in structured_content: {tasks_creating_assets}")
    print(f"- Tasks with other content: {tasks_with_content}")
    
    # 5. Check the deliverable creation process
    print("\n5. DELIVERABLE CREATION:")
    print("-" * 20)
    
    deliverables_result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_result.data
    
    print(f"Found {len(deliverables)} deliverables")
    for i, deliverable in enumerate(deliverables, 1):
        print(f"{i}. Created: {deliverable.get('created_at', 'Unknown')}")
        print(f"   Title: {deliverable.get('title', 'No title')}")
        print(f"   Type: {deliverable.get('type', 'Unknown')}")
        print(f"   Quality Level: {deliverable.get('quality_level', 'Unknown')}")
        print(f"   Business Specificity Score: {deliverable.get('business_specificity_score', 'Unknown')}")
        print()
    
    # 6. Conclusion
    print("6. CONCLUSIONS:")
    print("-" * 20)
    
    if len(asset_creation_tasks) == len(tasks):
        print("✅ All tasks are 'Create Asset' tasks - this is correct behavior")
    else:
        print("⚠️  Mixed task types detected")
    
    if tasks_creating_subtasks == 0:
        print("✅ No tasks are creating sub-tasks - good!")
    else:
        print(f"❌ {tasks_creating_subtasks} tasks are creating sub-tasks instead of assets")
    
    if tasks_creating_assets > 0:
        print(f"✅ {tasks_creating_assets} tasks are creating assets in structured_content")
    else:
        print("❌ No tasks are creating assets in structured_content")
    
    if len(deliverables) > 0:
        print(f"✅ {len(deliverables)} deliverables have been created successfully")
        print("✅ The system IS working - tasks are producing assets and deliverables!")
    else:
        print("❌ No deliverables created")

if __name__ == "__main__":
    asyncio.run(analyze_workflow_pattern())