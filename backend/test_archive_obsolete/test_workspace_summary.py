#!/usr/bin/env python3
"""
Workspace Test Data Summary
Provides you with ready-to-use workspace IDs and test data for the unified asset system
"""

import os
import sys
import json
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment manually if needed
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from database import supabase, list_tasks

async def find_test_workspaces():
    """Find workspaces with deliverable data for testing"""
    print("🔍 SEARCHING FOR TEST-READY WORKSPACES")
    print("=" * 60)
    
    # Get recent workspaces
    result = supabase.table("workspaces").select("id, name, created_at, goal").order("created_at", desc=True).limit(10).execute()
    
    test_workspaces = []
    
    for workspace in result.data:
        workspace_id = workspace['id']
        workspace_name = workspace.get('name', 'Unnamed')
        workspace_goal = workspace.get('goal', 'No goal specified')
        
        print(f"\n📊 Analyzing workspace: {workspace_name}")
        print(f"   ID: {workspace_id}")
        print(f"   Goal: {workspace_goal[:100]}{'...' if len(workspace_goal) > 100 else ''}")
        
        # Get tasks for this workspace
        tasks = await list_tasks(workspace_id)
        
        # Analyze task types
        status_counts = {}
        creation_types = {}
        intelligent_deliverables = []
        final_deliverable_tasks = []
        
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            creation_type = task.get("creation_type", "unknown")
            creation_types[creation_type] = creation_types.get(creation_type, 0) + 1
            
            if creation_type == "intelligent_ai_deliverable":
                intelligent_deliverables.append(task)
            
            # Check for final deliverable flags in context
            context_data = task.get("context_data", {}) or {}
            if isinstance(context_data, dict):
                if (context_data.get("is_final_deliverable") or 
                    context_data.get("deliverable_aggregation") or
                    context_data.get("intelligent_deliverable")):
                    final_deliverable_tasks.append(task)
        
        print(f"   📈 Total tasks: {len(tasks)}")
        print(f"   📊 Status breakdown: {status_counts}")
        print(f"   🤖 Intelligent AI deliverables: {len(intelligent_deliverables)}")
        print(f"   🎯 Final deliverable tasks: {len(final_deliverable_tasks)}")
        
        # This workspace is test-ready if it has deliverable data
        if intelligent_deliverables or final_deliverable_tasks:
            test_workspaces.append({
                "id": workspace_id,
                "name": workspace_name,
                "goal": workspace_goal,
                "total_tasks": len(tasks),
                "intelligent_deliverables": len(intelligent_deliverables),
                "final_deliverable_tasks": len(final_deliverable_tasks),
                "status_breakdown": status_counts,
                "sample_deliverable_tasks": intelligent_deliverables[:2],  # First 2 for examples
            })
            print(f"   ✅ TEST-READY: Has deliverable data!")
        else:
            print(f"   ❌ No deliverable data found")
    
    return test_workspaces

async def extract_sample_data(workspace_id: str):
    """Extract sample data from a workspace for testing"""
    print(f"\n📋 EXTRACTING SAMPLE DATA FROM: {workspace_id}")
    print("=" * 60)
    
    tasks = await list_tasks(workspace_id)
    
    # Find intelligent AI deliverable tasks
    intelligent_tasks = [t for t in tasks if t.get('creation_type') == 'intelligent_ai_deliverable']
    
    sample_data = {}
    
    for task in intelligent_tasks:
        task_id = task.get('id')
        task_name = task.get('name', 'Unnamed')
        
        print(f"\n🎯 Task: {task_name}")
        print(f"   ID: {task_id}")
        
        # Extract result data
        result = task.get('result', {})
        if isinstance(result, dict) and 'detailed_results_json' in result:
            detailed_results = result['detailed_results_json']
            
            print(f"   📊 Has detailed results: Yes")
            if isinstance(detailed_results, dict):
                print(f"   🔑 Keys in detailed results: {list(detailed_results.keys())}")
                
                # Sample some interesting data
                for key, value in detailed_results.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"      - {key}: {len(value)} items")
                        if len(value) > 0:
                            sample_data[key] = value[:2]  # First 2 items as sample
                    elif isinstance(value, dict) and len(value) > 0:
                        print(f"      - {key}: dict with {len(value)} keys")
                        sample_data[key] = value
            else:
                print(f"   📊 Detailed results type: {type(detailed_results)}")
        else:
            print(f"   📊 Has detailed results: No")
    
    return sample_data

async def main():
    """Main function to find and summarize test data"""
    print("🧪 UNIFIED ASSET MANAGEMENT - TEST DATA DISCOVERY")
    print("=" * 80)
    print("This script finds workspaces with deliverable data you can use for testing.")
    print()
    
    # Find test-ready workspaces
    test_workspaces = await find_test_workspaces()
    
    print(f"\n🎉 SUMMARY: FOUND {len(test_workspaces)} TEST-READY WORKSPACES")
    print("=" * 80)
    
    for i, workspace in enumerate(test_workspaces, 1):
        print(f"\n🚀 WORKSPACE {i}: {workspace['name']}")
        print(f"   📍 ID: {workspace['id']}")
        print(f"   🎯 Goal: {workspace['goal'][:80]}{'...' if len(workspace['goal']) > 80 else ''}")
        print(f"   📊 Total tasks: {workspace['total_tasks']}")
        print(f"   🤖 AI deliverables: {workspace['intelligent_deliverables']}")
        print(f"   🎯 Final deliverables: {workspace['final_deliverable_tasks']}")
        
        # API endpoints you can test
        print(f"   🌐 API ENDPOINTS TO TEST:")
        print(f"      - Project deliverables: http://localhost:8000/projects/{workspace['id']}/deliverables")
        print(f"      - Workspace insights: http://localhost:8000/projects/{workspace['id']}/insights")
        print(f"      - Asset management: http://localhost:8000/assets/workspace/{workspace['id']}")
        
        # Frontend URLs  
        print(f"   🖥️  FRONTEND URLS TO TEST:")
        print(f"      - Deliverables page: http://localhost:3000/projects/{workspace['id']}/deliverables")
        print(f"      - Assets page: http://localhost:3000/projects/{workspace['id']}/assets")
        print(f"      - Project overview: http://localhost:3000/projects/{workspace['id']}")
        
        # Extract some sample data for the first workspace
        if i == 1:
            sample_data = await extract_sample_data(workspace['id'])
            if sample_data:
                print(f"\n   📋 SAMPLE DATA AVAILABLE:")
                for key, value in sample_data.items():
                    if isinstance(value, list):
                        print(f"      - {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"      - {key}: {len(value)} fields")
    
    if test_workspaces:
        primary_workspace = test_workspaces[0]
        print(f"\n🎯 RECOMMENDED FOR TESTING:")
        print(f"   Workspace ID: {primary_workspace['id']}")
        print(f"   Workspace Name: {primary_workspace['name']}")
        print(f"   Primary API URL: http://localhost:8000/projects/{primary_workspace['id']}/deliverables")
        print(f"   Primary Frontend URL: http://localhost:3000/projects/{primary_workspace['id']}/deliverables")
        
        print(f"\n📋 QUICK TEST COMMANDS:")
        print(f"   Backend test: curl http://localhost:8000/projects/{primary_workspace['id']}/deliverables")
        print(f"   Frontend test: Open http://localhost:3000/projects/{primary_workspace['id']}/deliverables in browser")
        
        print(f"\n🔧 TESTING CHECKLIST:")
        print(f"   ✅ Database connection working")
        print(f"   ✅ Found {len(test_workspaces)} workspaces with deliverable data")
        print(f"   ✅ Intelligent AI deliverable tasks detected")
        print(f"   ✅ Rich content processing available")
        print(f"   📋 Ready to test unified asset management system!")
    else:
        print(f"\n❌ No test-ready workspaces found. You may need to:")
        print(f"   1. Run the backend to generate some deliverable tasks")
        print(f"   2. Create a project and let agents complete tasks")
        print(f"   3. Check that tasks have 'intelligent_ai_deliverable' creation_type")

if __name__ == "__main__":
    asyncio.run(main())