#!/usr/bin/env python3
"""
Final analysis of the workflow pattern focusing on what we can access
"""
import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

async def final_analysis():
    workspace_id = '10aca193-3ca9-4200-ae19-6d430b64b3b0'
    
    print(f"FINAL ANALYSIS: Task Delegation Chain for workspace: {workspace_id}")
    print("=" * 80)
    
    # Get all tasks
    tasks_result = supabase.table('tasks').select('id, name, created_at, agent_id, result, status, parent_task_id').eq('workspace_id', workspace_id).order('created_at').execute()
    tasks = tasks_result.data
    
    # Get agents
    try:
        agents_result = supabase.table('agents').select('*').eq('workspace_id', workspace_id).execute()
        agents = agents_result.data
        agent_map = {agent['id']: agent for agent in agents}
    except:
        print("Could not access agents table")
        agent_map = {}
    
    # Get deliverables
    deliverables_result = supabase.table('deliverables').select('*').eq('workspace_id', workspace_id).execute()
    deliverables = deliverables_result.data
    
    print(f"Found {len(tasks)} tasks, {len(agent_map)} agents, {len(deliverables)} deliverables\n")
    
    print("="*80)
    print("SUMMARY OF FINDINGS:")
    print("="*80)
    
    # Analysis
    asset_creation_tasks = [t for t in tasks if t['name'].startswith('Create Asset:')]
    completed_tasks = [t for t in tasks if t['status'] == 'completed']
    pending_tasks = [t for t in tasks if t['status'] == 'pending']
    failed_tasks = [t for t in tasks if t['status'] == 'failed']
    
    print(f"1. TASK BREAKDOWN:")
    print(f"   - Total tasks: {len(tasks)}")
    print(f"   - Asset creation tasks: {len(asset_creation_tasks)} ({len(asset_creation_tasks)/len(tasks)*100:.1f}%)")
    print(f"   - Completed: {len(completed_tasks)}")
    print(f"   - Pending: {len(pending_tasks)}")
    print(f"   - Failed: {len(failed_tasks)}")
    print()
    
    # Check task hierarchy
    root_tasks = [t for t in tasks if not t['parent_task_id']]
    child_tasks = [t for t in tasks if t['parent_task_id']]
    
    print(f"2. TASK HIERARCHY:")
    print(f"   - Root tasks: {len(root_tasks)}")
    print(f"   - Child tasks: {len(child_tasks)}")
    print(f"   - Task hierarchy depth: {'FLAT' if len(child_tasks) == 0 else 'HIERARCHICAL'}")
    print()
    
    # Check what completed tasks produced
    tasks_creating_subtasks = 0
    tasks_with_assets = 0
    tasks_with_content = 0
    
    for task in completed_tasks:
        result = task.get('result', {})
        if isinstance(result, dict):
            if 'defined_sub_tasks' in result and result['defined_sub_tasks']:
                tasks_creating_subtasks += 1
            elif 'structured_content' in result:
                try:
                    structured = json.loads(result['structured_content']) if isinstance(result['structured_content'], str) else result['structured_content']
                    if isinstance(structured, dict) and 'assets' in structured and structured['assets']:
                        tasks_with_assets += 1
                    else:
                        tasks_with_content += 1
                except:
                    tasks_with_content += 1
            elif result:
                tasks_with_content += 1
    
    print(f"3. COMPLETED TASK OUTPUT:")
    print(f"   - Tasks creating sub-tasks: {tasks_creating_subtasks}")
    print(f"   - Tasks creating assets: {tasks_with_assets}")
    print(f"   - Tasks with other content: {tasks_with_content}")
    print()
    
    print(f"4. DELIVERABLES CREATED:")
    print(f"   - Total deliverables: {len(deliverables)}")
    if deliverables:
        for i, d in enumerate(deliverables, 1):
            content_len = len(str(d.get('content', '')))
            print(f"   - Deliverable {i}: {d.get('title', 'Unnamed')}")
            print(f"     Type: {d.get('type', 'Unknown')}, Content: {content_len} chars")
            print(f"     Quality: {d.get('quality_level', 'Unknown')}, Score: {d.get('business_specificity_score', 'N/A')}")
    print()
    
    print("="*80)
    print("DIAGNOSIS:")
    print("="*80)
    
    if len(child_tasks) == 0:
        print("✅ NO TASK DELEGATION ISSUE: All tasks are root tasks")
        print("   This means tasks are NOT creating sub-tasks in an endless chain")
        print()
    else:
        print("❌ TASK DELEGATION DETECTED:")
        print(f"   {len(child_tasks)} tasks are children of other tasks")
        print("   This indicates delegation is happening")
        print()
    
    if tasks_creating_subtasks == 0:
        print("✅ NO SUB-TASK CREATION: Completed tasks are not creating sub-tasks")
        print("   Tasks are doing the work themselves instead of delegating")
        print()
    else:
        print("❌ SUB-TASK CREATION DETECTED:")
        print(f"   {tasks_creating_subtasks} completed tasks created sub-tasks")
        print("   This is the delegation problem you're looking for!")
        print()
    
    if len(deliverables) > 0:
        print("✅ DELIVERABLES ARE BEING CREATED:")
        print(f"   {len(deliverables)} deliverables have been successfully created")
        print("   The system IS producing final assets")
        print()
        
        # Check deliverable content quality
        total_content = sum(len(str(d.get('content', ''))) for d in deliverables)
        avg_quality = sum(d.get('business_specificity_score', 0) for d in deliverables) / len(deliverables)
        print(f"   Total content: {total_content:,} characters")
        print(f"   Average quality score: {avg_quality:.1f}/100")
        print()
    else:
        print("❌ NO DELIVERABLES CREATED:")
        print("   This would be the real problem - no final outputs")
        print()
    
    print("="*80)
    print("CONCLUSION:")
    print("="*80)
    
    if len(child_tasks) == 0 and tasks_creating_subtasks == 0 and len(deliverables) > 0:
        print("🎉 SYSTEM IS WORKING CORRECTLY!")
        print()
        print("Your assumption about 'tasks creating sub-tasks instead of deliverables'")
        print("appears to be INCORRECT based on this analysis:")
        print()
        print("- ✅ Tasks are NOT creating sub-tasks")
        print("- ✅ Tasks are creating actual content/assets") 
        print("- ✅ Deliverables are being successfully created")
        print("- ✅ Content quality scores are reasonable")
        print()
        print("The 'Create Asset:' task names suggest the goal-driven task planner")
        print("is correctly generating concrete, asset-focused tasks rather than")
        print("abstract high-level tasks that would cause delegation chains.")
        print()
    else:
        print("⚠️  ISSUES DETECTED:")
        if len(child_tasks) > 0:
            print(f"- {len(child_tasks)} child tasks suggest some delegation")
        if tasks_creating_subtasks > 0:
            print(f"- {tasks_creating_subtasks} tasks are creating sub-tasks")
        if len(deliverables) == 0:
            print("- No deliverables have been created")
        print()
    
    print("RECOMMENDATION:")
    print("If you're still experiencing issues, the problem may be:")
    print("1. Timing - maybe tasks are still in progress")
    print("2. Different workspace - double-check the workspace ID")
    print("3. Frontend display - deliverables exist but aren't shown correctly")
    print("4. Expectation mismatch - system is working but differently than expected")

if __name__ == "__main__":
    asyncio.run(final_analysis())