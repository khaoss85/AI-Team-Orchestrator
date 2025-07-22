#!/usr/bin/env python3
"""
Debug agent data format issue
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database import list_agents

async def debug_agent_data():
    """Debug the format of agent data returned from database"""
    
    workspace_id = "f0bf116b-8fe9-4fcc-a5b4-2f819a4088fd"
    
    print(f"🔍 Debugging agent data for workspace: {workspace_id}")
    
    try:
        agents = await list_agents(workspace_id)
        
        print(f"✅ Found {len(agents)} agents")
        print(f"📊 Type of agents: {type(agents)}")
        
        for i, agent in enumerate(agents):
            print(f"\n🤖 Agent {i+1}:")
            print(f"   Type: {type(agent)}")
            print(f"   Value: {agent}")
            
            if isinstance(agent, dict):
                print(f"   Keys: {list(agent.keys())}")
                print(f"   ID: {agent.get('id', 'NO ID')}")
                print(f"   Name: {agent.get('name', 'NO NAME')}")
            elif isinstance(agent, list):
                print(f"   ❌ ERROR: Agent is a list with {len(agent)} elements!")
                print(f"   List contents: {agent}")
            else:
                print(f"   ❌ ERROR: Unexpected type!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agent_data())