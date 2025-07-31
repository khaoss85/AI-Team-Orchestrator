#!/usr/bin/env python3
"""
🔬 DIRECT SPECIALIST TEST
Test diretto del specialist_minimal per vedere se funziona
"""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_specialist_direct():
    """Test diretto del SpecialistAgent minimal"""
    
    try:
        from ai_agents.specialist_minimal import SpecialistAgent
        from models import Agent as AgentModel, Task, TaskStatus
        
        print("🧪 Testing SpecialistAgent directly...")
        
        # Create a minimal agent model
        now = datetime.now()
        agent_data = AgentModel(
            id=uuid4(),
            workspace_id=uuid4(),
            name="Test Agent",
            role="Developer",
            seniority="junior",
            status="available",
            created_at=now,
            updated_at=now
        )
        
        # Create minimal task
        task = Task(
            id=uuid4(),
            workspace_id=agent_data.workspace_id,
            name="Simple test task",
            description="Complete this simple test and respond with JSON",
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now
        )
        
        print("✅ Models created successfully")
        
        # Create specialist agent
        specialist = SpecialistAgent(agent_data)
        print("✅ SpecialistAgent created")
        
        # Execute task with timeout
        print("🚀 Executing task...")
        try:
            result = await asyncio.wait_for(
                specialist.execute(task),
                timeout=30.0  # 30 second timeout
            )
            
            print(f"✅ Task completed! Status: {result.status}")
            print(f"Summary: {result.summary}")
            print(f"Result: {result.result[:100]}...")
            
            return True
            
        except asyncio.TimeoutError:
            print("❌ Task execution timed out after 30 seconds")
            return False
        except Exception as e:
            print(f"❌ Task execution failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

async def main():
    """Main test"""
    print("🔬 DIRECT SPECIALIST TEST")
    print("=" * 50)
    
    success = await test_specialist_direct()
    
    if success:
        print("🎉 SpecialistAgent works correctly!")
    else:
        print("❌ SpecialistAgent has issues")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())