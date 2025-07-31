#!/usr/bin/env python3
"""
🔬 ISOLATED RUNNER TEST
Test diretto del Runner SDK per identificare la vera root cause
"""

import asyncio
import logging
import time
from agents import Agent, Runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_runner_directly():
    """Test diretto del Runner per vedere se il problema è lì"""
    
    print("🧪 Testing OpenAI Agents SDK Runner directly...")
    
    try:
        # Create a very simple agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent. Respond with valid JSON: {\"status\": \"completed\", \"result\": \"test successful\"}",
            model="gpt-3.5-turbo"
        )
        
        print("✅ Agent created successfully")
        
        # Test with simple task
        simple_task = "Complete this test task and respond with the required JSON format."
        
        print("🚀 Running simple task...")
        start_time = time.time()
        
        # Test with timeout to see if it hangs
        try:
            run_result = await asyncio.wait_for(
                Runner.run(agent, simple_task, max_turns=3),
                timeout=30.0  # 30 second timeout
            )
            
            execution_time = time.time() - start_time
            print(f"✅ Runner completed in {execution_time:.2f}s")
            print(f"Result: {run_result.final_output}")
            
            return True
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            print(f"❌ Runner TIMED OUT after {execution_time:.2f}s")
            print("🔍 This confirms Runner.run() is hanging!")
            
            return False
            
    except Exception as e:
        print(f"❌ Error in runner test: {e}")
        return False

async def main():
    """Main test execution"""
    print("🔬 ISOLATED RUNNER TEST - Checking if Runner.run() hangs")
    print("=" * 60)
    
    success = await test_runner_directly()
    
    if success:
        print("✅ Runner works correctly - problem is elsewhere")
    else:
        print("❌ Runner is hanging - this is the root cause!")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())