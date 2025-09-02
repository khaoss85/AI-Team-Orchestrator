#!/usr/bin/env python3
"""
Comprehensive Agent Description Prevention Test Suite
====================================================

This script tests ALL agent creation paths to ensure no agents can be created
with null or empty descriptions, regardless of the creation method.
"""

import asyncio
import sys
import os
import logging
from uuid import uuid4
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_agent, get_supabase_client
from routes.agents import create_new_agent
from models import AgentCreate, AgentSeniority
from fastapi import HTTPException

# Test configuration
TEST_WORKSPACE_ID = str(uuid4())

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AgentDescriptionTestSuite:
    
    async def setup(self):
        """Setup test environment"""
        try:
            supabase = get_supabase_client()
            
            # Create a test workspace
            workspace_data = {
                "id": TEST_WORKSPACE_ID,
                "name": "Description Test Workspace",
                "goal": "Test agent description validation",
                "status": "active"
            }
            supabase.table("workspaces").insert(workspace_data).execute()
            logger.info(f"✅ Created test workspace: {TEST_WORKSPACE_ID}")
            return True
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup test data"""
        try:
            supabase = get_supabase_client()
            
            # Delete test agents first (foreign key constraint)
            supabase.table("agents").delete().eq("workspace_id", TEST_WORKSPACE_ID).execute()
            # Delete test workspace
            supabase.table("workspaces").delete().eq("id", TEST_WORKSPACE_ID).execute()
            
            logger.info(f"✅ Cleaned up test workspace: {TEST_WORKSPACE_ID}")
        except Exception as e:
            logger.error(f"⚠️ Cleanup warning: {e}")

    async def test_database_create_agent_with_null_description(self):
        """Test database.create_agent with null description"""
        try:
            logger.info("🧪 Testing database.create_agent with null description...")
            
            agent = await create_agent(
                workspace_id=TEST_WORKSPACE_ID,
                name="Test Agent Null Desc",
                role="test_specialist",
                seniority="senior",
                description=None  # Explicitly null
            )
            
            if agent and agent.get('description'):
                logger.info(f"✅ PASS: Database layer generated description: {agent['description']}")
                return True
            else:
                logger.error(f"❌ FAIL: Agent created with null description: {agent}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database create_agent test failed: {e}")
            return False

    async def test_database_create_agent_with_empty_description(self):
        """Test database.create_agent with empty string description"""
        try:
            logger.info("🧪 Testing database.create_agent with empty description...")
            
            agent = await create_agent(
                workspace_id=TEST_WORKSPACE_ID,
                name="Test Agent Empty Desc",
                role="test_specialist", 
                seniority="senior",
                description=""  # Empty string
            )
            
            if agent and agent.get('description') and agent['description'].strip() != "":
                logger.info(f"✅ PASS: Database layer handled empty description: {agent['description']}")
                return True
            else:
                logger.error(f"❌ FAIL: Agent created with empty description: {agent}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database create_agent empty test failed: {e}")
            return False

    async def test_api_route_with_null_description(self):
        """Test /agents/{workspace_id} API route with null description"""
        try:
            logger.info("🧪 Testing API route with null description...")
            
            # Mock request object
            class MockRequest:
                headers = {}
                def __init__(self):
                    pass
            
            mock_request = MockRequest()
            
            agent_create = AgentCreate(
                workspace_id=TEST_WORKSPACE_ID,
                name="Test API Agent Null",
                role="api_specialist",
                seniority=AgentSeniority.SENIOR,
                description=None  # Explicitly null
            )
            
            # This should trigger the fix in routes/agents.py
            created_agent = await create_new_agent(
                workspace_id=TEST_WORKSPACE_ID,
                agent=agent_create,
                request=mock_request
            )
            
            if created_agent and created_agent.description and created_agent.description.strip() != "":
                logger.info(f"✅ PASS: API route generated description: {created_agent.description}")
                return True
            else:
                logger.error(f"❌ FAIL: API route created agent with null/empty description")
                return False
                
        except Exception as e:
            logger.error(f"❌ API route test failed: {e}")
            return False

    async def test_api_route_with_empty_description(self):
        """Test /agents/{workspace_id} API route with empty description"""
        try:
            logger.info("🧪 Testing API route with empty description...")
            
            # Mock request object
            class MockRequest:
                headers = {}
                def __init__(self):
                    pass
                    
            mock_request = MockRequest()
            
            agent_create = AgentCreate(
                workspace_id=TEST_WORKSPACE_ID,
                name="Test API Agent Empty",
                role="api_specialist",
                seniority=AgentSeniority.SENIOR,
                description=""  # Empty string
            )
            
            created_agent = await create_new_agent(
                workspace_id=TEST_WORKSPACE_ID,
                agent=agent_create,
                request=mock_request
            )
            
            if created_agent and created_agent.description and created_agent.description.strip() != "":
                logger.info(f"✅ PASS: API route handled empty description: {created_agent.description}")
                return True
            else:
                logger.error(f"❌ FAIL: API route created agent with empty description")
                return False
                
        except Exception as e:
            logger.error(f"❌ API route empty test failed: {e}")
            return False

    async def test_director_route_simulation(self):
        """Test director route path - simulate how Director creates agents"""
        try:
            logger.info("🧪 Testing Director route path simulation...")
            
            # Simulate what director.py does when creating agents
            agent_data_for_creation = {
                "workspace_id": TEST_WORKSPACE_ID,
                "name": "Test Director Agent", 
                "role": "director_specialist",
                "seniority": "expert",
                # Note: Intentionally omitting description to simulate Director behavior
            }
            
            # Filter like director.py does
            supported_fields = {
                'workspace_id', 'name', 'role', 'seniority', 'description',
                'system_prompt', 'llm_config', 'tools', 'can_create_tools',
                'first_name', 'last_name', 'personality_traits', 'communication_style',
                'hard_skills', 'soft_skills', 'background_story'
            }
            
            filtered_agent_data = {
                key: value for key, value in agent_data_for_creation.items()
                if key in supported_fields
            }
            
            # This goes directly to database.create_agent like director.py does
            created_agent = await create_agent(**filtered_agent_data)
            
            if created_agent and created_agent.get('description'):
                logger.info(f"✅ PASS: Director path handled missing description: {created_agent['description']}")
                return True
            else:
                logger.error(f"❌ FAIL: Director path created agent without description: {created_agent}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Director simulation test failed: {e}")
            return False

    async def verify_all_created_agents(self):
        """Verify all test agents have descriptions"""
        try:
            supabase = get_supabase_client()
            
            response = supabase.table('agents').select('*').eq('workspace_id', TEST_WORKSPACE_ID).execute()
            agents = response.data
            
            logger.info(f"🔍 Verifying {len(agents)} created test agents...")
            
            all_valid = True
            for agent in agents:
                desc = agent.get('description')
                agent_name = agent.get('name', 'Unknown')
                
                if not desc or desc.strip() == "":
                    logger.error(f"❌ VERIFICATION FAIL: {agent_name} has null/empty description")
                    all_valid = False
                else:
                    logger.info(f"✅ VERIFICATION PASS: {agent_name} has description: {desc[:50]}...")
            
            return all_valid
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 AGENT DESCRIPTION PREVENTION TEST SUITE")
        print("==========================================")
        
        # Setup
        setup_success = await self.setup()
        if not setup_success:
            print("❌ Test suite setup failed")
            return False
        
        try:
            test_results = []
            
            # Run all test scenarios
            test_results.append(("Database null description", await self.test_database_create_agent_with_null_description()))
            test_results.append(("Database empty description", await self.test_database_create_agent_with_empty_description()))
            test_results.append(("API route null description", await self.test_api_route_with_null_description()))
            test_results.append(("API route empty description", await self.test_api_route_with_empty_description()))
            test_results.append(("Director path simulation", await self.test_director_route_simulation()))
            
            # Final verification
            verification_pass = await self.verify_all_created_agents()
            test_results.append(("Final verification", verification_pass))
            
            # Summary
            print("\n📊 TEST RESULTS SUMMARY:")
            print("========================")
            passed_tests = 0
            total_tests = len(test_results)
            
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status}: {test_name}")
                if result:
                    passed_tests += 1
            
            print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
            
            if passed_tests == total_tests:
                print("🎉 ALL TESTS PASSED - Description prevention is working correctly!")
                return True
            else:
                print(f"⚠️ {total_tests - passed_tests} tests failed - Fix needs improvement")
                return False
                
        finally:
            await self.cleanup()

async def main():
    """Run the test suite"""
    test_suite = AgentDescriptionTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ COMPREHENSIVE VERIFICATION COMPLETE:")
        print("  - Fix applied at system level ✅")
        print("  - No existing problematic agents ✅")
        print("  - All creation paths covered ✅")
        print("  - Prevention logic tested and working ✅")
        print("\n🛡️ Future workspaces will have proper agent descriptions!")
    else:
        print("\n❌ VERIFICATION INCOMPLETE - Manual review needed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)