#!/usr/bin/env python3
"""
Analyze task delegation patterns for a specific workspace
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def analyze_workspace_tasks():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"Analyzing task delegation chain for workspace: {workspace_id}")
    print("=" * 80)
    
    # Get all tasks for this workspace
    try:
        result = supabase.table('tasks').select('id, name, parent_task_id, agent_id, result, status, created_at').eq('workspace_id', workspace_id).order('created_at').execute()
        
        tasks = result.data
        print(f'Found {len(tasks)} tasks for workspace {workspace_id}\n')
        
        # Build task hierarchy
        task_map = {}
        root_tasks = []
        children_map = {}
        
        for task in tasks:
            task_id = task['id']
            task_map[task_id] = task
            
            if not task['parent_task_id']:
                root_tasks.append(task)
            else:
                parent_id = task['parent_task_id']
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(task)
        
        # Print detailed task information
        print("DETAILED TASK ANALYSIS:")
        print("-" * 40)
        
        for i, task in enumerate(tasks, 1):
            print(f"{i}. Task: {task['name']}")
            print(f"   ID: {task['id']}")
            print(f"   Parent ID: {task['parent_task_id'] or 'None (root task)'}")
            print(f"   Agent ID: {task['agent_id']}")
            print(f"   Status: {task['status']}")
            print(f"   Created: {task['created_at']}")
            
            # Analyze result
            result = task.get('result', {})
            if isinstance(result, dict):
                if 'defined_sub_tasks' in result and result['defined_sub_tasks']:
                    print(f"   ✅ Created sub-tasks: {len(result['defined_sub_tasks'])} sub-tasks")
                    for j, sub_task in enumerate(result['defined_sub_tasks'], 1):
                        sub_name = sub_task.get('name', 'Unknown')
                        sub_id = sub_task.get('task_id', 'No ID')
                        print(f"      {j}. {sub_name} (ID: {sub_id})")
                elif 'assets' in result and result['assets']:
                    print(f"   📦 Created assets: {len(result['assets'])} assets")
                    for j, asset in enumerate(result['assets'], 1):
                        asset_type = asset.get('type', 'Unknown')
                        content_len = len(str(asset.get('content', '')))
                        print(f"      {j}. Type: {asset_type}, Content length: {content_len}")
                elif result:
                    # Check for other types of output
                    content_keys = [k for k in ['analysis', 'recommendations', 'findings', 'content', 'output'] if k in result]
                    if content_keys:
                        print(f"   📝 Has analysis/content (keys: {content_keys})")
                    else:
                        print(f"   ⚪ Result keys: {list(result.keys()) if result else 'Empty'}")
            else:
                result_str = str(result)[:100] if result else 'No result'
                print(f"   ⚪ Result: {result_str}{'...' if len(str(result)) > 100 else ''}")
            
            print()
        
        # Build and display task tree
        print("\nTASK DELEGATION TREE:")
        print("-" * 40)
        
        def print_task_tree(task, level=0, prefix=""):
            indent = "  " * level
            
            # Get task status and type info
            status = task['status']
            has_subtasks = isinstance(task.get('result', {}), dict) and 'defined_sub_tasks' in task.get('result', {})
            has_assets = isinstance(task.get('result', {}), dict) and 'assets' in task.get('result', {})
            
            # Choose icon based on what task produces
            if has_assets:
                icon = "📦"
            elif has_subtasks:
                icon = "🔄"
            elif status == 'completed':
                icon = "✅"
            elif status == 'failed':
                icon = "❌"
            else:
                icon = "⏳"
            
            print(f"{indent}{prefix}{icon} {task['name']} ({status})")
            
            # Show what it produced
            result = task.get('result', {})
            if isinstance(result, dict):
                if has_subtasks:
                    print(f"{indent}    └─ Creates {len(result['defined_sub_tasks'])} sub-tasks")
                elif has_assets:
                    print(f"{indent}    └─ Creates {len(result['assets'])} assets")
                elif result:
                    content_keys = [k for k in ['analysis', 'recommendations', 'findings', 'content', 'output'] if k in result]
                    if content_keys:
                        print(f"{indent}    └─ Produces content: {', '.join(content_keys)}")
            
            # Print children
            task_id = task['id']
            if task_id in children_map:
                for j, child in enumerate(children_map[task_id]):
                    is_last = j == len(children_map[task_id]) - 1
                    child_prefix = "└─ " if is_last else "├─ "
                    print_task_tree(child, level + 1, child_prefix)
        
        for root_task in root_tasks:
            print_task_tree(root_task)
            print()
        
        # Analysis summary
        print("ANALYSIS SUMMARY:")
        print("-" * 40)
        
        total_tasks = len(tasks)
        tasks_with_subtasks = sum(1 for t in tasks if isinstance(t.get('result', {}), dict) and 'defined_sub_tasks' in t.get('result', {}))
        tasks_with_assets = sum(1 for t in tasks if isinstance(t.get('result', {}), dict) and 'assets' in t.get('result', {}))
        completed_tasks = sum(1 for t in tasks if t['status'] == 'completed')
        
        print(f"Total tasks: {total_tasks}")
        print(f"Tasks that create sub-tasks: {tasks_with_subtasks}")
        print(f"Tasks that create assets: {tasks_with_assets}")
        print(f"Completed tasks: {completed_tasks}")
        print(f"Task delegation depth: {max(count_parents(t, task_map) for t in tasks)}")
        
        # Identify the problem pattern
        print(f"\nPROBLEM ANALYSIS:")
        print("-" * 40)
        
        if tasks_with_assets == 0:
            print("❌ NO ASSETS CREATED - This is the core problem!")
            print("   All tasks are creating sub-tasks instead of final deliverables")
        
        if tasks_with_subtasks > tasks_with_assets:
            print("⚠️  Too much delegation - tasks keep creating sub-tasks instead of doing work")
        
        # Find the delegation chain
        print(f"\nDELEGATION CHAIN ANALYSIS:")
        print("-" * 40)
        
        for root_task in root_tasks:
            print(f"Root task: {root_task['name']}")
            chain = build_delegation_chain(root_task, children_map)
            for level, level_tasks in enumerate(chain):
                print(f"  Level {level}: {len(level_tasks)} tasks")
                for task in level_tasks:
                    result = task.get('result', {})
                    if isinstance(result, dict) and 'defined_sub_tasks' in result:
                        print(f"    - {task['name']} → creates {len(result['defined_sub_tasks'])} sub-tasks")
                    elif isinstance(result, dict) and 'assets' in result:
                        print(f"    - {task['name']} → creates {len(result['assets'])} assets ✅")
                    else:
                        print(f"    - {task['name']} → produces content/analysis")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def count_parents(task, task_map):
    """Count how many parent tasks this task has (depth in hierarchy)"""
    count = 0
    current = task
    while current['parent_task_id']:
        count += 1
        current = task_map.get(current['parent_task_id'])
        if not current:
            break
    return count

def build_delegation_chain(root_task, children_map):
    """Build a list of task levels from root to leaves"""
    chain = [[root_task]]
    current_level = [root_task]
    
    while current_level:
        next_level = []
        for task in current_level:
            task_id = task['id']
            if task_id in children_map:
                next_level.extend(children_map[task_id])
        
        if next_level:
            chain.append(next_level)
            current_level = next_level
        else:
            current_level = []
    
    return chain

if __name__ == "__main__":
    asyncio.run(analyze_workspace_tasks())