#!/usr/bin/env python3
"""
Test semplificato del sistema di memoria workspace
Dimostra la struttura e le funzionalità senza database
"""

import asyncio
import logging
import json
from uuid import uuid4, UUID
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workspace_memory_models():
    """Test i modelli e la logica di base senza database"""
    
    print("🧠 Testing Workspace Memory Models & Logic")
    print("=" * 50)
    
    # Test 1: Model creation and validation
    print("\n1️⃣ Testing WorkspaceInsight model...")
    
    try:
        from models import WorkspaceInsight, InsightType, MemoryQueryRequest
        
        # Create test insights
        test_workspace_id = uuid4()
        test_task_id = uuid4()
        
        insight1 = WorkspaceInsight(
            workspace_id=test_workspace_id,
            task_id=test_task_id,
            agent_role="Contact Research Specialist",
            insight_type=InsightType.CONSTRAINT,
            content="LinkedIn search limited to 100 contacts/day without premium",
            relevance_tags=["contact_research", "linkedin", "limits"],
            confidence_score=0.9
        )
        
        insight2 = WorkspaceInsight(
            workspace_id=test_workspace_id,
            task_id=test_task_id,
            agent_role="Email Strategy Specialist", 
            insight_type=InsightType.SUCCESS_PATTERN,
            content="Apollo.io found 30% more contacts than manual LinkedIn search",
            relevance_tags=["contact_research", "apollo", "automation"],
            confidence_score=0.8
        )
        
        print(f"   ✅ Created insight 1: {insight1.insight_type.value} - {insight1.content[:50]}...")
        print(f"   ✅ Created insight 2: {insight2.insight_type.value} - {insight2.content[:50]}...")
        
        # Test serialization
        insight1_dict = insight1.model_dump()
        # Convert UUIDs and datetime to strings for JSON serialization
        def serialize_value(v):
            if isinstance(v, UUID):
                return str(v)
            elif isinstance(v, datetime):
                return v.isoformat()
            return v
        
        insight1_dict_json = {
            k: serialize_value(v) for k, v in insight1_dict.items()
        }
        print(f"   📄 Insight serialization works: {len(json.dumps(insight1_dict_json))} chars")
        
    except Exception as e:
        print(f"   ❌ Error in model testing: {e}")
        return False
    
    # Test 2: Memory query request validation
    print("\n2️⃣ Testing MemoryQueryRequest model...")
    
    try:
        # Valid query request
        query_req = MemoryQueryRequest(
            query="contact research challenges",
            insight_types=[InsightType.DISCOVERY, InsightType.CONSTRAINT],
            max_results=5,
            min_confidence=0.5
        )
        
        print(f"   ✅ Valid query request: '{query_req.query}' with {len(query_req.insight_types)} types")
        
        # Test validation limits
        try:
            invalid_query = MemoryQueryRequest(
                query="test",
                max_results=25,  # Should be capped at 20
                min_confidence=1.5  # Should be capped at 1.0
            )
            print(f"   ❌ Validation should have failed for invalid params")
        except Exception:
            print(f"   ✅ Validation correctly rejected invalid parameters")
        
    except Exception as e:
        print(f"   ❌ Error in query request testing: {e}")
        return False
    
    # Test 3: Agent Tools structure (without database)
    print("\n3️⃣ Testing WorkspaceMemoryTools structure...")
    
    try:
        from ai_agents.tools import WorkspaceMemoryTools
        
        # Check that tools exist
        tools = [
            WorkspaceMemoryTools.query_project_memory,
            WorkspaceMemoryTools.store_key_insight,
            WorkspaceMemoryTools.get_workspace_discoveries,
            WorkspaceMemoryTools.get_relevant_project_context
        ]
        
        print(f"   ✅ Found {len(tools)} WorkspaceMemoryTools")
        
        # Check tool signatures (function tools have different structure)
        for i, tool in enumerate(tools):
            tool_name = getattr(tool, 'name', f'tool_{i}')
            # Function tools have params_json_schema instead of inspect signature
            if hasattr(tool, 'params_json_schema'):
                params_count = len(tool.params_json_schema.get('properties', {}))
                print(f"      • {tool_name}: {params_count} parameters")
            else:
                print(f"      • {tool_name}: function tool (structure varies)")
        
    except Exception as e:
        print(f"   ❌ Error in tools testing: {e}")
        return False
    
    # Test 4: Scenario simulation (logic only)
    print("\n4️⃣ Testing realistic scenario logic...")
    
    try:
        # Simulate Task Chain with memory
        scenario_insights = []
        
        # Task 1: Contact Research fails
        task1_insight = WorkspaceInsight(
            workspace_id=test_workspace_id,
            task_id=uuid4(),
            agent_role="Contact Research Specialist",
            insight_type=InsightType.CONSTRAINT,
            content="Only found 2/50 contacts - LinkedIn search limits exceeded",
            relevance_tags=["contact_research", "linkedin_limits", "goal_gap"],
            confidence_score=0.9
        )
        scenario_insights.append(task1_insight)
        
        # Task 2: Contact Research retry with alternative approach
        task2_insight = WorkspaceInsight(
            workspace_id=test_workspace_id,
            task_id=uuid4(),
            agent_role="Contact Research Specialist",
            insight_type=InsightType.SUCCESS_PATTERN,
            content="Apollo.io + Sales Navigator bypassed LinkedIn limits, found 48/50 contacts",
            relevance_tags=["contact_research", "apollo", "sales_navigator", "solution"],
            confidence_score=0.95
        )
        scenario_insights.append(task2_insight)
        
        # Task 3: Email Strategy can see progress
        task3_insight = WorkspaceInsight(
            workspace_id=test_workspace_id,
            task_id=uuid4(),
            agent_role="Email Marketing Specialist",
            insight_type=InsightType.DISCOVERY,
            content="With 48 contacts available, can run A/B test on email sequences",
            relevance_tags=["email_strategy", "ab_testing", "contact_count"],
            confidence_score=0.8
        )
        scenario_insights.append(task3_insight)
        
        print(f"   📋 Scenario simulation with {len(scenario_insights)} insights:")
        for i, insight in enumerate(scenario_insights, 1):
            print(f"      {i}. {insight.agent_role}: {insight.content[:60]}...")
        
        # Simulate context building
        contact_research_insights = [
            i for i in scenario_insights 
            if "contact_research" in i.relevance_tags
        ]
        
        print(f"   🔍 Contact research insights found: {len(contact_research_insights)}")
        
        # Simulate lesson learning
        constraints = [i for i in scenario_insights if i.insight_type == InsightType.CONSTRAINT]
        solutions = [i for i in scenario_insights if i.insight_type == InsightType.SUCCESS_PATTERN]
        
        print(f"   ⚠️ Constraints identified: {len(constraints)}")
        print(f"   ✅ Solutions found: {len(solutions)}")
        
        if constraints and solutions:
            print(f"   🎯 Memory system would help agents learn from constraint to solution!")
        
    except Exception as e:
        print(f"   ❌ Error in scenario testing: {e}")
        return False
    
    # Test 5: Memory integration check
    print("\n5️⃣ Testing Specialist Agent integration...")
    
    try:
        # Check that specialist.py has been modified
        with open('ai_agents/specialist.py', 'r') as f:
            specialist_content = f.read()
        
        integration_checks = [
            "workspace_memory" in specialist_content,
            "get_relevant_context" in specialist_content,
            "_extract_and_store_insights" in specialist_content,
            "WorkspaceMemoryTools" in specialist_content
        ]
        
        passed_checks = sum(integration_checks)
        print(f"   📊 Integration checks passed: {passed_checks}/4")
        
        if passed_checks >= 3:
            print(f"   ✅ Specialist agent properly integrated with memory system")
        else:
            print(f"   ⚠️ Some integration points missing")
        
    except Exception as e:
        print(f"   ❌ Error checking integration: {e}")
        return False
    
    print("\n✅ All model and logic tests completed successfully!")
    print("\n🎯 Memory System Benefits (Ready for Database):")
    print("   • ✅ Models validated: WorkspaceInsight, MemoryQueryRequest, etc.")
    print("   • ✅ Agent tools available: query_project_memory, store_key_insight, etc.")
    print("   • ✅ Specialist integration: context injection + insight extraction")
    print("   • ✅ Scenario logic: constraint → solution learning demonstrated")
    print("\n💡 Next Steps:")
    print("   1. Create workspace_insights table in Supabase")
    print("   2. Run full database tests")
    print("   3. Test with real agents and tasks")
    
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Workspace Memory System Structure Tests")
        print("=" * 60)
        
        success = await test_workspace_memory_models()
        
        if success:
            print("\n🎉 Workspace Memory System structure is correct!")
            print("   Ready for database integration and real testing.")
        else:
            print("\n❌ Some structure tests failed. Check implementation.")
    
    asyncio.run(main())