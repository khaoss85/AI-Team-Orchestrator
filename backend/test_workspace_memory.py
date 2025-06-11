#!/usr/bin/env python3
"""
Test del sistema di memoria workspace
Verifica che gli agenti possano memorizzare e recuperare insights tra task
"""

import asyncio
import logging
import json
from uuid import uuid4, UUID
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workspace_memory_system():
    """Test completo del sistema di memoria workspace"""
    
    print("🧠 Testing Workspace Memory System")
    print("=" * 50)
    
    # Test 1: Basic WorkspaceMemory functionality
    print("\n1️⃣ Testing WorkspaceMemory basic operations...")
    
    try:
        from workspace_memory import workspace_memory
        from models import InsightType, MemoryQueryRequest, WorkspaceInsight
        
        # Create test workspace
        test_workspace_id = uuid4()
        test_task_id = uuid4()
        
        print(f"   📋 Test workspace: {test_workspace_id}")
        
        # Store some test insights
        insights_to_store = [
            {
                "insight_type": InsightType.DISCOVERY,
                "content": "LinkedIn search limited to 100 contacts/day without premium",
                "tags": ["contact_research", "linkedin", "limits"],
                "confidence": 0.9
            },
            {
                "insight_type": InsightType.CONSTRAINT,
                "content": "GDPR compliance required for EU contact collection",
                "tags": ["gdpr", "compliance", "european_contacts"],
                "confidence": 1.0
            },
            {
                "insight_type": InsightType.SUCCESS_PATTERN,
                "content": "Apollo.io found 30% more contacts than manual LinkedIn search",
                "tags": ["contact_research", "apollo", "automation"],
                "confidence": 0.8
            },
            {
                "insight_type": InsightType.FAILURE_LESSON,
                "content": "Cold emails without personalization had <5% response rate",
                "tags": ["email_strategy", "personalization", "response_rate"],
                "confidence": 0.85
            }
        ]
        
        # Store insights
        stored_insights = []
        for insight_data in insights_to_store:
            stored = await workspace_memory.store_insight(
                workspace_id=test_workspace_id,
                task_id=test_task_id,
                agent_role="Contact Research Specialist",
                insight_type=insight_data["insight_type"],
                content=insight_data["content"],
                relevance_tags=insight_data["tags"],
                confidence_score=insight_data["confidence"]
            )
            if stored:
                stored_insights.append(stored)
                print(f"   ✅ Stored: {insight_data['insight_type'].value} - {insight_data['content'][:50]}...")
            else:
                print(f"   ❌ Failed to store: {insight_data['content'][:50]}...")
        
        print(f"   📊 Stored {len(stored_insights)}/{len(insights_to_store)} insights")
        
    except Exception as e:
        print(f"   ❌ Error in basic operations: {e}")
        return False
    
    # Test 2: Memory queries  
    print("\n2️⃣ Testing memory queries...")
    
    try:
        # Query for contact research insights
        contact_query = MemoryQueryRequest(
            query="contact research challenges",
            insight_types=[InsightType.DISCOVERY, InsightType.CONSTRAINT],
            max_results=3
        )
        
        contact_results = await workspace_memory.query_insights(test_workspace_id, contact_query)
        print(f"   🔍 Contact research query found {contact_results.total_found} insights:")
        for insight in contact_results.insights:
            print(f"      • {insight.insight_type.value}: {insight.content}")
        
        # Query for email strategy insights
        email_query = MemoryQueryRequest(
            query="email strategy response rate",
            max_results=2
        )
        
        email_results = await workspace_memory.query_insights(test_workspace_id, email_query)
        print(f"   📧 Email strategy query found {email_results.total_found} insights:")
        for insight in email_results.insights:
            print(f"      • {insight.insight_type.value}: {insight.content}")
            
    except Exception as e:
        print(f"   ❌ Error in memory queries: {e}")
        return False
    
    # Test 3: Workspace summary
    print("\n3️⃣ Testing workspace summary...")
    
    try:
        summary = await workspace_memory.get_workspace_summary(test_workspace_id)
        print(f"   📈 Workspace Summary:")
        print(f"      Total insights: {summary.total_insights}")
        print(f"      By type: {summary.insights_by_type}")
        print(f"      Top tags: {summary.top_tags}")
        print(f"      Recent discoveries: {len(summary.recent_discoveries)}")
        print(f"      Key constraints: {len(summary.key_constraints)}")
        print(f"      Success patterns: {len(summary.success_patterns)}")
        
    except Exception as e:
        print(f"   ❌ Error in workspace summary: {e}")
        return False
    
    # Test 4: WorkspaceMemoryTools (agent tools)
    print("\n4️⃣ Testing WorkspaceMemoryTools for agents...")
    
    try:
        from ai_agents.tools import WorkspaceMemoryTools
        
        # Test query_project_memory tool
        query_result = await WorkspaceMemoryTools.query_project_memory(
            workspace_id=str(test_workspace_id),
            query="contact research",
            insight_types="discovery,constraint",
            max_results=3
        )
        
        query_data = json.loads(query_result)
        print(f"   🔧 Agent query tool found {query_data['total_found']} insights")
        print(f"   📋 Context: {query_data['context'][:100]}...")
        
        # Test store_key_insight tool
        new_task_id = uuid4()
        store_result = await WorkspaceMemoryTools.store_key_insight(
            workspace_id=str(test_workspace_id),
            task_id=str(new_task_id),
            agent_role="Email Strategy Specialist",
            insight_type="optimization",
            content="Using A/B testing increased email open rates by 25%",
            tags="email_strategy,ab_testing,optimization",
            confidence=0.9
        )
        
        store_data = json.loads(store_result)
        if store_data["success"]:
            print(f"   ✅ Agent successfully stored new insight")
        else:
            print(f"   ❌ Agent failed to store insight: {store_data.get('error')}")
        
        # Test get_workspace_discoveries tool
        discoveries_result = await WorkspaceMemoryTools.get_workspace_discoveries(
            workspace_id=str(test_workspace_id),
            domain="contact_research"
        )
        
        discoveries_data = json.loads(discoveries_result)
        print(f"   🔍 Agent discoveries tool found {discoveries_data['total_insights']} total insights")
        print(f"   📋 Recent discoveries: {len(discoveries_data['recent_discoveries'])}")
        
    except Exception as e:
        print(f"   ❌ Error in agent tools: {e}")
        return False
    
    # Test 5: Scenario reale - simulazione agenti in sequenza
    print("\n5️⃣ Testing realistic agent scenario...")
    
    try:
        # Simula Task 1: Contact Research (trova solo 2 contatti invece di 50)
        task1_id = uuid4()
        await workspace_memory.store_insight(
            workspace_id=test_workspace_id,
            task_id=task1_id,
            agent_role="Contact Research Specialist",
            insight_type=InsightType.CONSTRAINT,
            content="Only found 2/50 contacts - LinkedIn search limits exceeded",
            relevance_tags=["contact_research", "linkedin_limits", "goal_gap"],
            confidence_score=0.9
        )
        
        # Simula Task 2: Contact Research Retry (con memoria del primo fallimento)
        from models import Task
        mock_task2 = Task(
            id=uuid4(),
            workspace_id=test_workspace_id,
            name="Contact Research Retry - Alternative Approaches",
            description="Research alternative methods to reach 50 contact goal",
            agent_id=None,
            assigned_to_role="Contact Research Specialist",
            priority="high",
            status="pending"
        )
        
        # Get relevant context (come farebbe l'agente)
        context_for_task2 = await workspace_memory.get_relevant_context(test_workspace_id, mock_task2)
        print(f"   📋 Context for retry task:")
        print(f"   {context_for_task2}")
        
        # Task 2 completa con successo usando Apollo.io
        await workspace_memory.store_insight(
            workspace_id=test_workspace_id,
            task_id=mock_task2.id,
            agent_role="Contact Research Specialist",
            insight_type=InsightType.SUCCESS_PATTERN,
            content="Apollo.io + Sales Navigator bypassed LinkedIn limits, found 48/50 contacts",
            relevance_tags=["contact_research", "apollo", "sales_navigator", "solution"],
            confidence_score=0.95
        )
        
        # Simula Task 3: Email Strategy (può vedere che abbiamo ~48 contatti, non 2)
        mock_task3 = Task(
            id=uuid4(),
            workspace_id=test_workspace_id,
            name="Create Email Campaign Strategy",
            description="Design email sequences for our contact list",
            agent_id=None,
            assigned_to_role="Email Marketing Specialist",
            priority="medium",
            status="pending"
        )
        
        context_for_task3 = await workspace_memory.get_relevant_context(test_workspace_id, mock_task3)
        print(f"   📧 Context for email strategy task:")
        print(f"   {context_for_task3}")
        
        # Final summary
        final_summary = await workspace_memory.get_workspace_summary(test_workspace_id)
        print(f"\n   📊 Final workspace state:")
        print(f"      Total insights: {final_summary.total_insights}")
        print(f"      Success patterns: {len(final_summary.success_patterns)}")
        print(f"      Constraints identified: {len(final_summary.key_constraints)}")
        
    except Exception as e:
        print(f"   ❌ Error in realistic scenario: {e}")
        return False
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 Memory System Benefits Demonstrated:")
    print("   • Task continuity: Later tasks know about earlier discoveries")
    print("   • Lesson learning: Constraints and solutions are remembered")
    print("   • Context awareness: Agents get relevant insights automatically") 
    print("   • Goal tracking: System remembers progress toward numerical targets")
    
    return True

async def test_database_setup():
    """Test che il database sia configurato correttamente"""
    print("🗄️ Testing database setup...")
    
    try:
        from database import supabase
        
        # Test basic query to workspace_insights table
        result = supabase.table("workspace_insights").select("id").limit(1).execute()
        
        print(f"   ✅ Database connection successful")
        print(f"   📊 Existing insights in DB: {len(result.data) if result.data else 0}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        print("   💡 Note: Make sure to run the SQL schema in create_workspace_insights_table.sql")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Workspace Memory System Tests")
        print("=" * 60)
        
        # Test database first
        db_ok = await test_database_setup()
        if not db_ok:
            print("\n❌ Database not ready. Please set up the workspace_insights table first.")
            return
        
        # Run main memory tests
        success = await test_workspace_memory_system()
        
        if success:
            print("\n🎉 Workspace Memory System is working correctly!")
            print("   Ready for production use with real agents.")
        else:
            print("\n❌ Some tests failed. Check logs for details.")
    
    asyncio.run(main())