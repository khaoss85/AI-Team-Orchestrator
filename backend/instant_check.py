import asyncio
import os
from database import supabase
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def instant_check():
    print("🔍 INSTANT SYSTEM CHECK")
    print("=" * 30)
    
    # Environment check
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    
    # Quick task status check
    statuses = ['pending', 'in_progress', 'completed']
    for status in statuses:
        response = await asyncio.to_thread(
            supabase.table("tasks").select("id").eq("status", status).execute
        )
        print(f"{status.upper()}: {len(response.data)} tasks")
    
    # Check if we have in_progress tasks with agents
    response = await asyncio.to_thread(
        supabase.table("tasks").select("*").eq("status", "in_progress").limit(1).execute
    )
    
    if response.data:
        task = response.data[0]
        print(f"\nIn-progress task: {task['name']}")
        print(f"Agent ID: {task.get('agent_id', 'None')}")
        print(f"Updated: {task.get('updated_at', 'Unknown')}")
        
        # Check if agent exists
        if task.get('agent_id'):
            agent_response = await asyncio.to_thread(
                supabase.table("agents").select("*").eq("id", task['agent_id']).execute
            )
            if agent_response.data:
                agent = agent_response.data[0]
                print(f"Agent: {agent['name']} ({agent['status']})")
            else:
                print("❌ Agent not found")
    
    # Check for any completed tasks
    response = await asyncio.to_thread(
        supabase.table("tasks").select("*").eq("status", "completed").execute
    )
    
    if response.data:
        print(f"\n✅ {len(response.data)} completed tasks found!")
        for task in response.data[:2]:
            print(f"  - {task['name']}")
    else:
        print("\n❌ No completed tasks found")
    
    # Check deliverables/assets
    response = await asyncio.to_thread(
        supabase.table("asset_artifacts").select("*").execute
    )
    print(f"\nAsset artifacts: {len(response.data)}")
    
    if response.data:
        print("Recent artifacts:")
        for artifact in response.data[:2]:
            print(f"  - {artifact.get('name', 'Unnamed')}")

# Run immediately
asyncio.run(instant_check())