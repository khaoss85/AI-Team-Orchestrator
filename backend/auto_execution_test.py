#!/usr/bin/env python3
"""
Auto-executing test for task execution
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def test_now():
    print("🧪 AUTO EXECUTION TEST")
    print("="*30)
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    
    if not api_key:
        print("❌ Cannot test without API key")
        return False
    
    # Import database
    from database import supabase
    
    # Get task in progress
    response = await asyncio.to_thread(
        supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
    )
    
    if not response.data:
        print("❌ No tasks in progress")
        return False
    
    task = response.data[0]
    print(f"📋 Task: {task['name']}")
    print(f"👤 Agent: {task['agent_id']}")
    
    # Test imports
    try:
        from ai_agents.manager import AgentManager
        print("✅ AgentManager imported")
        
        manager = AgentManager()
        print("✅ AgentManager initialized")
        
        # Test method exists
        if hasattr(manager, 'execute_agent_task'):
            print("✅ execute_agent_task method exists")
        else:
            print("❌ execute_agent_task method missing")
            return False
        
        # Try execution
        print("🚀 Testing execution...")
        result = await manager.execute_agent_task(
            agent_id=task['agent_id'],
            task_id=task['id'],
            task_name=task['name'],
            task_description=task.get('description', ''),
            workspace_id=task['workspace_id']
        )
        
        if result:
            print(f"✅ SUCCESS: {result}")
            
            # Check task status
            response = await asyncio.to_thread(
                supabase.table("tasks").select("*").eq("id", task['id']).execute
            )
            
            if response.data:
                updated_task = response.data[0]
                print(f"📊 Task status: {updated_task['status']}")
                if updated_task['status'] == 'completed':
                    print("🎉 TASK COMPLETED!")
                    return True
                else:
                    print(f"⚠️ Task still {updated_task['status']}")
                    return False
            else:
                print("❌ Could not check task status")
                return False
        else:
            print("❌ No result from execution")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Auto-run when imported
if __name__ == "__main__":
    result = asyncio.run(test_now())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}")
    exit(0 if result else 1)