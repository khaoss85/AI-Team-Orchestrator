#!/usr/bin/env python3

"""
Debug the current director call to see exactly what's happening with budget parsing
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal, BudgetConstraint
from uuid import uuid4
import logging

# Configure logging to see debug details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_director_call():
    """Debug the director call to see budget processing details"""
    
    print("🔍 DEBUGGING DIRECTOR BUDGET PROCESSING")
    print("=" * 50)
    
    # Create the exact request that frontend sends
    budget_constraint = BudgetConstraint(max_cost=10000.0, currency="EUR")
    
    proposal_request = DirectorTeamProposal(
        workspace_id=uuid4(),
        workspace_goal="Creare una strategia di lead generation B2B per acquisire 100 contatti qualificati di CMO e CTO in aziende SaaS con 50-200 dipendenti. Configurare HubSpot CRM, creare sequenze email personalizzate e gestire il nurturing dei lead.",
        user_feedback="",
        budget_constraint=budget_constraint,
        budget_limit=None,  # This should be calculated from budget_constraint
        requirements=None
    )
    
    print(f"📤 Created proposal request:")
    print(f"   workspace_id: {proposal_request.workspace_id}")
    print(f"   budget_constraint: {proposal_request.budget_constraint}")
    print(f"   budget_limit: {proposal_request.budget_limit}")
    
    if proposal_request.budget_constraint:
        print(f"   budget_constraint.max_cost: {proposal_request.budget_constraint.max_cost}")
        print(f"   budget_constraint.currency: {proposal_request.budget_constraint.currency}")
    
    try:
        # Create director and make the call
        director = DirectorAgent()
        
        print("\n🎯 Calling DirectorAgent.create_team_proposal()...")
        proposal = await director.create_team_proposal(proposal_request)
        
        print(f"\n✅ PROPOSAL CREATED SUCCESSFULLY!")
        print(f"   Agent count: {len(proposal.agents)}")
        print(f"   Agent roles: {[agent.role for agent in proposal.agents]}")
        print(f"   Estimated cost: {proposal.estimated_cost}")
        
        # Check if agents have estimated_monthly_cost now
        for i, agent in enumerate(proposal.agents):
            seniority = agent.seniority if hasattr(agent, 'seniority') else 'unknown'
            cost = agent.estimated_monthly_cost if hasattr(agent, 'estimated_monthly_cost') else 'MISSING'
            print(f"   Agent {i+1}: {agent.role} ({seniority}) - €{cost}/month")
            
        # Calculate expected team size for 10k budget
        expected_team_size = min(8, max(3, int(10000 / 1500)))
        actual_team_size = len(proposal.agents)
        
        print(f"\n📊 BUDGET ANALYSIS:")
        print(f"   Budget: €10,000")
        print(f"   Expected team size: {expected_team_size} agents")
        print(f"   Actual team size: {actual_team_size} agents")
        
        if actual_team_size >= expected_team_size:
            print(f"   ✅ SUCCESS: Budget parsing worked correctly!")
        else:
            print(f"   ❌ ISSUE: Team size too small, suggests fallback logic")
            
    except Exception as e:
        print(f"❌ Error during director call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_director_call())