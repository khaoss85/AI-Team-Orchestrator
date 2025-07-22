#!/usr/bin/env python3
"""
Simple test to verify task execution works
"""

import asyncio
import os
from dotenv import load_dotenv
from database import supabase

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def simple_test():
    print("🧪 SIMPLE EXECUTION TEST")
    print("="*30)
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    
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
    
    # Test agent manager import
    try:
        from ai_agents.manager import AgentManager
        manager = AgentManager()
        print("✅ AgentManager imported")
        
        # Test if execute_agent_task exists
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
            return True
        else:
            print("❌ No result")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(simple_test())
    print(f"\n{'✅ SUCCESS' if result else '❌ FAILURE'}")
    exit(0 if result else 1)