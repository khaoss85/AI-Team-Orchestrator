#!/usr/bin/env python3
"""
Simple test to check if the system is working
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
load_dotenv()

async def test_system():
    print("🔍 SIMPLE SYSTEM TEST")
    print("=" * 30)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"✅ API Key: {'Available' if api_key else 'Missing'}")
    
    # Test database connection
    try:
        from database import supabase
        response = await asyncio.to_thread(
            supabase.table("workspaces").select("id").limit(1).execute
        )
        print(f"✅ Database: Connected ({len(response.data)} workspaces)")
    except Exception as e:
        print(f"❌ Database: Error - {e}")
        return False
    
    # Test agent creation
    try:
        from ai_agents.specialist_sdk_complete import SpecialistAgent
        from models import Agent, AgentStatus
        import uuid
        from datetime import datetime
        
        # Create a simple agent model
        agent_data = Agent(
            id=str(uuid.uuid4()),
            workspace_id=str(uuid.uuid4()),
            name="TestAgent",
            role="tester",
            seniority="junior",
            skills=["testing"],
            personality_traits=["detail-oriented"],
            hard_skills=[],
            soft_skills=[],
            status=AgentStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Try to create agent
        specialist = SpecialistAgent(
            agent_data=agent_data,
            all_workspace_agents_data=[agent_data]
        )
        
        print(f"✅ Agent Creation: Success ({specialist.agent_data.name})")
        
    except Exception as e:
        print(f"❌ Agent Creation: Error - {e}")
        return False
    
    print("\n🎉 SYSTEM BASIC CHECKS PASSED!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)