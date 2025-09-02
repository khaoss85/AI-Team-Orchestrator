#!/usr/bin/env python3
"""
Test script to reproduce the frontend team display issue.
This will test the full flow: create workspace -> generate team -> check response.
"""

import asyncio
import json
import uuid
from models import DirectorTeamProposal
from ai_agents.director import DirectorAgent

async def test_team_generation_issue():
    """Test the team generation with 10,000 EUR budget to reproduce the issue."""
    
    # Generate a test workspace ID
    test_workspace_id = str(uuid.uuid4())
    print(f"🧪 Testing team generation for workspace: {test_workspace_id}")
    
    # Create the director proposal request
    director_request = DirectorTeamProposal(
        id=uuid.uuid4(),
        workspace_id=uuid.UUID(test_workspace_id),
        workspace_goal=None,
        user_feedback=None,
        budget_constraint=None,
        extracted_goals=None,
        budget_limit=10000.0,  # 10,000 EUR budget
        requirements='Creare una strategia di lead generation B2B per acquisire 100 contatti qualificati di CMO e CTO in aziende SaaS con 50-200 dipendenti. Configurare HubSpot CRM, creare sequenze email personalizzate e gestire il nurturing dei lead.',
        agents=[],
        handoffs=[],
        estimated_cost={},
        rationale=None
    )
    
    print(f"💰 Budget: {director_request.budget_limit} EUR")
    print(f"📋 Requirements: {director_request.requirements}")
    
    # Create director agent and generate proposal
    director = DirectorAgent()
    
    try:
        print("\n🤖 Generating team proposal...")
        result = await director.create_team_proposal(director_request)
        
        print(f"\n✅ Team proposal generated successfully!")
        print(f"📊 Team size: {len(result.agents)} agents")
        print(f"💶 Total cost: {result.estimated_cost.get('total_estimated_cost', result.estimated_cost.get('total', 0))} EUR")
        
        # Display team breakdown
        print(f"\n👥 Team composition:")
        for i, agent in enumerate(result.agents, 1):
            print(f"  {i}. {agent.get('name', 'Unknown')} - {agent.get('role', 'Unknown Role')} ({agent.get('seniority', 'unknown')})")
        
        # Display cost breakdown
        print(f"\n💰 Cost breakdown:")
        breakdown = result.estimated_cost.get('breakdown_by_agent', result.estimated_cost.get('breakdown', {}))
        if breakdown:
            for agent_name, cost in breakdown.items():
                print(f"  - {agent_name}: {cost} EUR")
        else:
            print("  - No cost breakdown available")
        
        # Convert to JSON for frontend inspection
        print(f"\n🔍 JSON Response (first 1000 chars):")
        response_json = {
            "agents": result.agents,
            "handoffs": result.handoffs,
            "estimated_cost": result.estimated_cost,
            "rationale": result.rationale
        }
        json_str = json.dumps(response_json, indent=2)
        print(json_str[:1000] + "..." if len(json_str) > 1000 else json_str)
        
        # Check for potential issues
        print(f"\n🔍 Issue Analysis:")
        print(f"  - Expected team size for 10K budget: 6 agents")
        print(f"  - Actual team size: {len(result.agents)} agents")
        print(f"  - Backend correctly generates 6 agents: {'✅ YES' if len(result.agents) == 6 else '❌ NO'}")
        print(f"  - Has cost data: {'✅ YES' if result.estimated_cost else '❌ NO'}")
        print(f"  - Cost > 0: {'✅ YES' if result.estimated_cost.get('total_estimated_cost', result.estimated_cost.get('total', 0)) > 0 else '❌ NO'}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating team proposal: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Testing Frontend Team Display Issue")
    print("=" * 50)
    
    result = asyncio.run(test_team_generation_issue())
    
    print("\n" + "=" * 50)
    if result and len(result.agents) == 6:
        print("✅ BACKEND WORKS CORRECTLY: Generates 6 agents for 10K budget")
        print("🔍 ISSUE IS IN FRONTEND: Check API response processing or error handling")
    elif result and len(result.agents) != 6:
        print(f"❌ BACKEND ISSUE: Generated {len(result.agents)} agents instead of 6")
    else:
        print("❌ BACKEND ERROR: Could not generate team proposal")