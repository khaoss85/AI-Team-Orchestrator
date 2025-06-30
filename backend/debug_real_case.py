#!/usr/bin/env python3
"""
Debug the actual case causing the error by reproducing the exact database scenario
"""

import asyncio
import json
import traceback
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

from fix_deliverable_creation import extract_concrete_deliverables_ai_driven
from database import supabase

async def debug_real_case():
    """Debug using real data from the workspace"""
    
    print("🧪 Fetching real data from workspace bc41beb3-4380-434a-8280-92821006840e...")
    
    try:
        # Get real goals from the database
        goals_response = supabase.table('workspace_goals').select('*').eq('workspace_id', 'bc41beb3-4380-434a-8280-92821006840e').execute()
        
        if not goals_response.data:
            print("No goals found")
            return
        
        print(f"Found {len(goals_response.data)} goals")
        
        # Get real tasks
        tasks_response = supabase.table('tasks').select('*').eq('workspace_id', 'bc41beb3-4380-434a-8280-92821006840e').execute()
        
        print(f"Found {len(tasks_response.data)} tasks")
        
        # Find a task with actual detailed_results_json that could be causing the issue
        for task in tasks_response.data:
            if task.get('result') and isinstance(task['result'], dict):
                detailed_results = task['result'].get('detailed_results_json')
                if detailed_results and detailed_results != '{}':
                    print(f"\\n🎯 Testing task: {task['name']}")
                    print(f"   Result keys: {list(task['result'].keys())}")
                    
                    # Test with first available goal
                    test_goal = goals_response.data[0]
                    print(f"   Goal: {test_goal['description']}")
                    
                    try:
                        print("   📝 Calling extract_concrete_deliverables_ai_driven...")
                        result = await extract_concrete_deliverables_ai_driven(detailed_results, test_goal)
                        print(f"   ✅ Success: {len(result)} deliverables extracted")
                        
                        for i, item in enumerate(result):
                            print(f"     {i+1}. Type: {item.get('type', 'unknown')}")
                            print(f"         Name: {item.get('name', 'N/A')}")
                    
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                        print("   Full traceback:")
                        traceback.print_exc()
                        
                        # Print the problematic detailed_results for analysis
                        print(f"\\n🔍 Problematic detailed_results_json:")
                        if isinstance(detailed_results, str):
                            print(f"Type: string, Length: {len(detailed_results)}")
                            print(f"Preview: {detailed_results[:500]}...")
                        else:
                            print(f"Type: {type(detailed_results)}")
                            print(f"Content: {detailed_results}")
                        
                        return  # Stop at first error to analyze
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_real_case())