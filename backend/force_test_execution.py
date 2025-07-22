#!/usr/bin/env python3
"""
Force execution of a task to test the complete E2E flow
"""

import asyncio
import os
from dotenv import load_dotenv
from database import supabase
from datetime import datetime

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def force_test_execution():
    print("🚀 FORCING TASK EXECUTION TEST")
    print("=" * 40)
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # Get first task in progress
    response = await asyncio.to_thread(
        supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
    )
    
    if not response.data:
        print("❌ No tasks in progress")
        return False
    
    task = response.data[0]
    print(f"📋 Task: {task['name']}")
    print(f"👤 Agent: {task['agent_id']}")
    print(f"🏢 Workspace: {task['workspace_id']}")
    
    # Get agent details
    agent_response = await asyncio.to_thread(
        supabase.table("agents").select("*").eq("id", task['agent_id']).execute
    )
    
    if not agent_response.data:
        print("❌ Agent not found")
        return False
    
    agent = agent_response.data[0]
    print(f"✅ Agent: {agent['name']} ({agent['role']})")
    
    # Try to execute the task
    try:
        print("\n🔧 Attempting direct task execution...")
        
        # Import agent manager
        from ai_agents.manager import AgentManager
        
        manager = AgentManager()
        print("✅ AgentManager initialized")
        
        # Execute task
        import time
        start_time = time.time()
        
        result = await manager.execute_agent_task(
            agent_id=task['agent_id'],
            task_id=task['id'],
            task_name=task['name'],
            task_description=task.get('description', ''),
            workspace_id=task['workspace_id']
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ Execution time: {execution_time:.2f}s")
        
        if result:
            print(f"✅ Task executed successfully!")
            print(f"📊 Result: {result}")
            
            # Check task status
            updated_response = await asyncio.to_thread(
                supabase.table("tasks").select("*").eq("id", task['id']).execute
            )
            
            if updated_response.data:
                updated_task = updated_response.data[0]
                print(f"📈 Task status: {updated_task['status']}")
                
                if updated_task['status'] == 'completed':
                    print("🎉 TASK COMPLETED!")
                    
                    # Check for generated artifacts
                    artifact_response = await asyncio.to_thread(
                        supabase.table("asset_artifacts").select("*").eq("task_id", task['id']).execute
                    )
                    
                    if artifact_response.data:
                        print(f"📦 Generated {len(artifact_response.data)} artifacts:")
                        for artifact in artifact_response.data:
                            print(f"  - {artifact.get('name', 'Unnamed')}")
                    else:
                        print("📦 No artifacts generated")
                    
                    return True
                else:
                    print(f"⚠️ Task status: {updated_task['status']}")
                    return False
            else:
                print("❌ Could not verify task status")
                return False
        else:
            print("❌ Task execution returned no result")
            return False
            
    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Execute immediately when imported
if __name__ == "__main__":
    result = asyncio.run(force_test_execution())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}: Force execution test")
    exit(0 if result else 1)