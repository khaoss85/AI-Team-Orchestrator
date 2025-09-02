#!/usr/bin/env python3
"""
Test script to debug B2B team size generation issue.
Expected: 10,000 EUR budget should generate 6 agents, but only getting 3.
"""

import asyncio
import os
import sys
import json
import logging
from uuid import uuid4

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('director_team_size_debug.log')
    ]
)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal

async def test_b2b_proposal():
    """Test that B2B lead generation projects get correct team size based on budget"""
    
    logger = logging.getLogger(__name__)
    director = DirectorAgent()
    
    # Test case: B2B lead generation project with 10,000 EUR budget
    budget = 10000.0
    expected_team_size = min(8, max(3, int(budget / 1500)))  # Should be 6
    
    b2b_request = DirectorTeamProposal(
        workspace_id=uuid4(),
        requirements="Creare una strategia di lead generation B2B per acquisire 100 contatti qualificati di CMO e CTO in aziende SaaS con 50-200 dipendenti. Configurare HubSpot CRM, creare sequenze email personalizzate e gestire il nurturing dei lead.",
        budget_limit=budget,
        agents=[],  # Will be filled by Director
        handoffs=[],
        estimated_cost={}
    )
    
    print("🔍 Testing B2B Team Size Generation...")
    print(f"📝 Project: B2B Lead Generation")
    print(f"💰 Budget: €{budget}")
    print(f"🎯 Expected team size: {expected_team_size} agents (based on budget/1500)")
    print("-" * 60)
    
    try:
        # Create proposal
        logger.info("Calling director.create_team_proposal()...")
        proposal = await director.create_team_proposal(b2b_request)
        
        actual_team_size = len(proposal.agents)
        print(f"\n📊 RESULTS:")
        print(f"👥 Actual Team Size: {actual_team_size} agents")
        print(f"🎯 Expected Team Size: {expected_team_size} agents")
        
        if actual_team_size < expected_team_size:
            print(f"❌ ISSUE DETECTED: Team is {expected_team_size - actual_team_size} agents SHORT!")
            print(f"   Budget supports {expected_team_size} agents but only {actual_team_size} were generated")
        else:
            print(f"✅ Team size is correct!")
            
        print(f"\n💵 Cost Analysis:")
        print(f"  Total Cost: €{proposal.estimated_cost.get('total_estimated_cost', 0)}")
        print(f"  Budget: €{budget}")
        print(f"  Utilization: {(proposal.estimated_cost.get('total_estimated_cost', 0) / budget * 100):.1f}%")
        
        print(f"\n📋 Team Composition:")
        
        for i, agent in enumerate(proposal.agents, 1):
            print(f"  {i}. {agent.name}")
            print(f"     Role: {agent.role}")
            print(f"     Seniority: {agent.seniority} (€{agent.estimated_monthly_cost}/month)")
            
        # Check for B2B-specific roles
        roles = [agent.role.lower() for agent in proposal.agents]
        b2b_indicators = ['business', 'research', 'email', 'sales', 'lead', 'crm', 'marketing', 'outbound']
        
        b2b_count = sum(1 for role in roles if any(ind in role for ind in b2b_indicators))
        
        print(f"\n📊 Domain Analysis:")
        print(f"  B2B-focused agents: {b2b_count}/{len(proposal.agents)}")
        
        if b2b_count >= len(proposal.agents) * 0.6:  # At least 60% B2B focused
            print("  ✅ Team is correctly B2B-focused")
        else:
            print("  ⚠️ Team may not be optimally B2B-focused")
            
        print(f"\n💭 Rationale: {proposal.rationale[:200]}...")
        
        # Save detailed output
        with open('director_proposal_debug.json', 'w') as f:
            json.dump({
                'expected_size': expected_team_size,
                'actual_size': actual_team_size,
                'budget': budget,
                'total_cost': proposal.estimated_cost.get('total_estimated_cost', 0),
                'agents': [
                    {
                        'name': agent.name,
                        'role': agent.role,
                        'seniority': str(agent.seniority),
                        'monthly_cost': agent.estimated_monthly_cost
                    }
                    for agent in proposal.agents
                ]
            }, f, indent=2)
        print("\n📁 Detailed output saved to director_proposal_debug.json")
        
    except Exception as e:
        logger.error(f"Error creating proposal: {e}", exc_info=True)
        print(f"\n❌ Error creating proposal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("DIRECTOR TEAM SIZE DEBUG TEST")
    print("=" * 60)
    asyncio.run(test_b2b_proposal())