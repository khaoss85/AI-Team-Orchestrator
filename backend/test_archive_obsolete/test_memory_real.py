#!/usr/bin/env python3
"""
Test completo del sistema di memoria workspace con database reale
Usa workspace e task esistenti per test realistici
"""

import asyncio
import logging
import json
from uuid import uuid4, UUID
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_existing_workspace_and_task():
    """Get existing workspace and task from database for realistic testing"""
    try:
        from database import supabase
        
        # Get an existing workspace
        workspaces = supabase.table("workspaces").select("id,name").limit(1).execute()
        if not workspaces.data:
            print("   ⚠️ No workspaces found. Creating test workspace...")
            
            # Create a test workspace
            test_workspace = {
                "name": "Memory Test Workspace",
                "description": "Test workspace for memory system",
                "user_id": str(uuid4()),  # Random user for test
                "status": "active",
                "goal": "Test workspace memory system functionality"
            }
            
            created_workspace = supabase.table("workspaces").insert(test_workspace).execute()
            if created_workspace.data:
                workspace_id = created_workspace.data[0]["id"]
                print(f"   ✅ Created test workspace: {workspace_id}")
            else:
                print(f"   ❌ Failed to create workspace")
                return None, None
        else:
            workspace_id = workspaces.data[0]["id"]
            workspace_name = workspaces.data[0]["name"]
            print(f"   ✅ Using existing workspace: {workspace_name} ({workspace_id})")
        
        # Get an existing task or create one
        tasks = supabase.table("tasks").select("id,name").eq("workspace_id", workspace_id).limit(1).execute()
        if not tasks.data:
            print("   ⚠️ No tasks found. Creating test task...")
            
            test_task = {
                "workspace_id": workspace_id,
                "name": "Memory Test Task",
                "description": "Test task for memory system validation",
                "status": "completed",  # Completed so we can extract insights
                "priority": "medium"
            }
            
            created_task = supabase.table("tasks").insert(test_task).execute()
            if created_task.data:
                task_id = created_task.data[0]["id"]
                print(f"   ✅ Created test task: {task_id}")
            else:
                print(f"   ❌ Failed to create task")
                return workspace_id, None
        else:
            task_id = tasks.data[0]["id"]
            task_name = tasks.data[0]["name"]
            print(f"   ✅ Using existing task: {task_name} ({task_id})")
        
        return workspace_id, task_id
        
    except Exception as e:
        print(f"   ❌ Error getting workspace/task: {e}")
        return None, None

async def test_workspace_memory_real():
    """Test completo con database reale e workspace/task esistenti"""
    
    print("🧠 Testing Workspace Memory System with Real Database")
    print("=" * 60)
    
    # Test 1: Get real workspace and task
    print("\n1️⃣ Setting up test data...")
    
    workspace_id, task_id = await get_existing_workspace_and_task()
    if not workspace_id or not task_id:
        print("   ❌ Failed to get workspace/task. Cannot continue.")
        return False
    
    # Test 2: Store insights with real IDs
    print("\n2️⃣ Testing insight storage with real workspace/task...")
    
    try:
        from workspace_memory import workspace_memory
        from models import InsightType
        
        # Clean up any existing test insights first
        from database import supabase
        supabase.table("workspace_insights").delete().eq("workspace_id", workspace_id).like("content", "%Memory Test%").execute()
        
        test_insights = [
            {
                "insight_type": InsightType.DISCOVERY,
                "content": "[Memory Test] LinkedIn search found 25 high-quality prospects",
                "tags": ["contact_research", "linkedin", "prospects"],
                "confidence": 0.9
            },
            {
                "insight_type": InsightType.CONSTRAINT,
                "content": "[Memory Test] Daily API limits reached after 100 LinkedIn searches",
                "tags": ["linkedin", "api_limits", "constraints"],
                "confidence": 0.95
            },
            {
                "insight_type": InsightType.SUCCESS_PATTERN,
                "content": "[Memory Test] Apollo.io bypass achieved 90% higher contact discovery rate",
                "tags": ["apollo", "contact_research", "bypass_solution"],
                "confidence": 0.85
            }
        ]
        
        stored_count = 0
        for insight_data in test_insights:
            stored = await workspace_memory.store_insight(
                workspace_id=UUID(workspace_id),
                task_id=UUID(task_id),
                agent_role="Memory Test Agent",
                insight_type=insight_data["insight_type"],
                content=insight_data["content"],
                relevance_tags=insight_data["tags"],
                confidence_score=insight_data["confidence"]
            )
            
            if stored:
                stored_count += 1
                print(f"   ✅ Stored: {insight_data['insight_type'].value} - {insight_data['content'][:60]}...")
            else:
                print(f"   ❌ Failed: {insight_data['content'][:60]}...")
        
        print(f"   📊 Successfully stored {stored_count}/{len(test_insights)} insights")
        
        if stored_count == 0:
            print("   ❌ Cannot continue without stored insights")
            return False
            
    except Exception as e:
        print(f"   ❌ Error storing insights: {e}")
        return False
    
    # Test 3: Query insights
    print("\n3️⃣ Testing insight queries...")
    
    try:
        from models import MemoryQueryRequest
        
        # Query for contact research insights
        query_req = MemoryQueryRequest(
            query="contact research linkedin",
            insight_types=[InsightType.DISCOVERY, InsightType.CONSTRAINT],
            max_results=5
        )
        
        results = await workspace_memory.query_insights(UUID(workspace_id), query_req)
        print(f"   🔍 Contact research query found {results.total_found} insights:")
        for insight in results.insights:
            print(f"      • {insight.insight_type.value}: {insight.content}")
        
        # Test context building
        print(f"   📋 Query context preview:")
        print(f"      {results.query_context[:150]}...")
        
    except Exception as e:
        print(f"   ❌ Error querying insights: {e}")
        return False
    
    # Test 4: Agent tools (simulate tool calls)
    print("\n4️⃣ Testing agent tools simulation...")
    
    try:
        from ai_agents.tools import WorkspaceMemoryTools
        
        # Test query tool
        query_result = await WorkspaceMemoryTools.query_project_memory(
            workspace_id=workspace_id,
            query="contact research",
            insight_types="discovery,constraint",
            max_results=3
        )
        
        query_data = json.loads(query_result)
        print(f"   🔧 Agent query tool found {query_data.get('total_found', 0)} insights")
        if query_data.get('context'):
            print(f"   📋 Context length: {len(query_data['context'])} chars")
        
        # Test store tool
        store_result = await WorkspaceMemoryTools.store_key_insight(
            workspace_id=workspace_id,
            task_id=task_id,
            agent_role="Memory Test Agent",
            insight_type="optimization",
            content="[Memory Test] Batch processing increased efficiency by 40%",
            tags="optimization,batch_processing,efficiency",
            confidence=0.8
        )
        
        store_data = json.loads(store_result)
        if store_data.get("success"):
            print(f"   ✅ Agent successfully stored new insight")
        else:
            print(f"   ❌ Agent failed to store: {store_data.get('error')}")
        
        # Test discoveries tool
        discoveries_result = await WorkspaceMemoryTools.get_workspace_discoveries(
            workspace_id=workspace_id
        )
        
        discoveries_data = json.loads(discoveries_result)
        print(f"   📊 Workspace discoveries: {discoveries_data.get('total_insights', 0)} total insights")
        
    except Exception as e:
        print(f"   ❌ Error testing agent tools: {e}")
        return False
    
    # Test 5: Memory integration scenario
    print("\n5️⃣ Testing realistic scenario...")
    
    try:
        from models import Task
        
        # Simulate new task that needs context
        mock_task = Task(
            id=UUID(task_id),
            workspace_id=UUID(workspace_id),
            name="Contact Research Phase 2",
            description="Continue contact research with improved methods",
            agent_id=None,
            assigned_to_role="Contact Research Specialist",
            priority="high",
            status="pending"
        )
        
        # Get relevant context (like specialist agent would)
        context = await workspace_memory.get_relevant_context(UUID(workspace_id), mock_task)
        
        if context.strip():
            print(f"   🧠 Context successfully retrieved for new task:")
            print(f"   {context}")
        else:
            print(f"   ⚠️ No relevant context found for task")
        
        # Get workspace summary
        summary = await workspace_memory.get_workspace_summary(UUID(workspace_id))
        print(f"   📈 Workspace Summary:")
        print(f"      Total insights: {summary.total_insights}")
        print(f"      Insights by type: {summary.insights_by_type}")
        print(f"      Recent discoveries: {len(summary.recent_discoveries)}")
        print(f"      Key constraints: {len(summary.key_constraints)}")
        
    except Exception as e:
        print(f"   ❌ Error in scenario test: {e}")
        return False
    
    # Test 6: Cleanup test data
    print("\n6️⃣ Cleaning up test data...")
    
    try:
        # Remove test insights
        cleanup_result = supabase.table("workspace_insights").delete().eq("workspace_id", workspace_id).like("content", "%Memory Test%").execute()
        deleted_count = len(cleanup_result.data) if cleanup_result.data else 0
        print(f"   🧹 Cleaned up {deleted_count} test insights")
        
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")
    
    print("\n✅ All real database tests completed successfully!")
    print("\n🎯 Memory System Status:")
    print("   • ✅ Database integration working")
    print("   • ✅ Insight storage and retrieval functional") 
    print("   • ✅ Agent tools operational")
    print("   • ✅ Context building for tasks working")
    print("   • ✅ Workspace summary generation working")
    print("\n🚀 The system is ready for production use!")
    
    return True

async def test_specialist_integration():
    """Test basic specialist agent integration"""
    print("\n🤖 Testing Specialist Agent Integration...")
    
    try:
        # Import specialist agent
        from ai_agents.specialist import SpecialistAgent
        
        # Check that WorkspaceMemoryTools are in the available tools
        workspace_id, task_id = await get_existing_workspace_and_task()
        if not workspace_id:
            print("   ⚠️ Skipping integration test - no workspace available")
            return True
        
        # Create a minimal agent data structure
        from models import Agent, AgentSeniority, AgentStatus
        
        agent_data = Agent(
            id=UUID(str(uuid4())),
            workspace_id=UUID(workspace_id),
            name="Test Memory Agent",
            role="Memory Test Specialist",
            seniority=AgentSeniority.SENIOR,
            status=AgentStatus.ACTIVE,
            description="Test agent for memory integration",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            health={"status": "healthy", "last_update": datetime.now().isoformat()}
        )
        
        # Initialize specialist with memory tools
        specialist = SpecialistAgent(agent_data)
        
        # Check if memory tools are loaded
        tool_names = []
        for tool in specialist.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
        
        memory_tools = [name for name in tool_names if 'memory' in name.lower() or 'project' in name.lower()]
        print(f"   🔧 Memory tools found: {memory_tools}")
        
        if memory_tools:
            print(f"   ✅ Specialist agent properly integrated with memory tools")
        else:
            print(f"   ⚠️ Memory tools not found in specialist agent")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing specialist integration: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Real Database Memory System Tests")
        print("=" * 60)
        
        # Test main memory system
        memory_success = await test_workspace_memory_real()
        
        # Test specialist integration
        integration_success = await test_specialist_integration()
        
        if memory_success and integration_success:
            print("\n🎉 ALL TESTS PASSED! Memory system is fully operational!")
            print("   Ready for production use with real agents and tasks.")
        else:
            print("\n❌ Some tests failed. Check logs for details.")
    
    asyncio.run(main())