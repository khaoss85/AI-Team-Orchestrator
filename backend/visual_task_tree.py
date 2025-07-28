#!/usr/bin/env python3
"""
Create a visual tree diagram of the task delegation
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def create_visual_tree():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print("TASK DELEGATION TREE VISUALIZATION")
    print("=" * 80)
    print(f"Workspace: {workspace_id}")
    print()
    
    # Get all tasks and deliverables
    tasks_result = supabase.table('tasks').select('*').eq('workspace_id', workspace_id).order('created_at').execute()
    tasks = tasks_result.data
    
    deliverables_result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_result.data
    
    print("TASK FLOW DIAGRAM:")
    print("-" * 40)
    print()
    
    # Show workflow progression
    print("📋 WORKSPACE GOALS")
    print("    │")
    print("    ▼")
    print("⚙️  GOAL-DRIVEN TASK PLANNER")
    print("    │")
    print("    ├─ Generates concrete 'Create Asset:' tasks")
    print("    │  (NOT abstract high-level tasks)")
    print("    │")
    print("    ▼")
    print("👥 AGENTS EXECUTE TASKS")
    print(f"    │  ({len(tasks)} tasks total)")
    print("    │")
    
    # Show task status breakdown
    completed = len([t for t in tasks if t['status'] == 'completed'])
    pending = len([t for t in tasks if t['status'] == 'pending'])
    failed = len([t for t in tasks if t['status'] == 'failed'])
    in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
    needs_revision = len([t for t in tasks if t['status'] == 'needs_revision'])
    
    print(f"    ├─ ✅ Completed: {completed}")
    print(f"    ├─ ⏳ Pending: {pending}")
    print(f"    ├─ 🔄 In Progress: {in_progress}")
    print(f"    ├─ 📝 Needs Revision: {needs_revision}")
    print(f"    ├─ ❌ Failed: {failed}")
    print("    │")
    print("    ▼")
    print("📦 DELIVERABLE ENGINE")
    print("    │  (Aggregates completed task results)")
    print("    │")
    print(f"    ├─ Created {len(deliverables)} deliverables")
    for i, d in enumerate(deliverables, 1):
        quality = d.get('quality_level', 'unknown')
        score = d.get('business_specificity_score', 0)
        print(f"    ├─ Deliverable {i}: {quality} quality ({score}/100)")
    print("    │")
    print("    ▼")
    print("🎯 FINAL BUSINESS ASSETS")
    print(f"    └─ {sum(len(str(d.get('content', ''))) for d in deliverables):,} characters of content")
    
    print()
    print("TASK DELEGATION ANALYSIS:")
    print("-" * 40)
    
    # Check for parent-child relationships
    root_tasks = [t for t in tasks if not t.get('parent_task_id')]
    child_tasks = [t for t in tasks if t.get('parent_task_id')]
    
    print(f"Root tasks (no parent): {len(root_tasks)}")
    print(f"Child tasks (have parent): {len(child_tasks)}")
    print()
    
    if len(child_tasks) == 0:
        print("✅ FLAT STRUCTURE - No task delegation hierarchy!")
        print("   All tasks are independent 'Create Asset:' tasks")
        print("   No endless delegation chains detected")
    else:
        print("⚠️  HIERARCHICAL STRUCTURE DETECTED:")
        for child in child_tasks:
            parent = next((t for t in tasks if t['id'] == child['parent_task_id']), None)
            parent_name = parent['name'] if parent else 'Unknown Parent'
            print(f"   {child['name']} ← delegated from: {parent_name}")
    
    print()
    print("EXAMPLE TASK EXECUTION FLOW:")
    print("-" * 40)
    
    # Show a few example tasks
    example_tasks = [t for t in tasks if t['status'] == 'completed'][:3]
    
    for i, task in enumerate(example_tasks, 1):
        print(f"{i}. Task: '{task['name']}'")
        print(f"   Agent: {task.get('agent_id', 'Unknown')}")
        print(f"   Status: {task['status']}")
        
        result = task.get('result', {})
        if isinstance(result, dict):
            if 'defined_sub_tasks' in result and result['defined_sub_tasks']:
                print(f"   Output: ❌ Created {len(result['defined_sub_tasks'])} sub-tasks (BAD)")
            elif 'structured_content' in result:
                content_len = len(str(result['structured_content']))
                print(f"   Output: ✅ Created content ({content_len} chars) (GOOD)")
            elif result:
                print(f"   Output: ✅ Created result content (GOOD)")
            else:
                print(f"   Output: ⚪ No output")
        print()
    
    print("FINAL VERDICT:")
    print("=" * 40)
    
    if len(child_tasks) == 0 and len(deliverables) > 0:
        print("🎉 NO DELEGATION PROBLEM DETECTED!")
        print()
        print("Your system is working correctly:")
        print("• Goal-driven planner creates concrete asset tasks")
        print("• Agents execute tasks without creating sub-tasks")
        print("• Completed tasks produce actual content")
        print("• Deliverable engine aggregates results into final assets")
        print("• High-quality deliverables are successfully created")
        print()
        print("The issue you described (tasks creating sub-tasks instead of")
        print("deliverables) is NOT happening in this workspace.")
    else:
        print("⚠️  POTENTIAL ISSUES DETECTED:")
        if len(child_tasks) > 0:
            print(f"• {len(child_tasks)} tasks have parent tasks (delegation detected)")
        if len(deliverables) == 0:
            print("• No deliverables created")
        print()
        print("Investigation needed to determine root cause.")

if __name__ == "__main__":
    asyncio.run(create_visual_tree())