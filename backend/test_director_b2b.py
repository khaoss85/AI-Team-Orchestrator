#!/usr/bin/env python3
"""
Test script to verify Director correctly identifies B2B projects
"""

import asyncio
import os
import sys
import json
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal

async def test_b2b_proposal():
    """Test that B2B lead generation projects get correct team composition"""
    
    director = DirectorAgent()
    
    # Test case: B2B lead generation project (Italian)
    b2b_request = DirectorTeamProposal(
        workspace_id=uuid4(),
        requirements="Raccogliere 20 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 4 sequenze email da impostare su Hubspot",
        budget_limit=10000.0,
        agents=[],  # Will be filled by Director
        handoffs=[],
        estimated_cost={}
    )
    
    print("🔍 Testing B2B Lead Generation Project...")
    print(f"📝 Project: {b2b_request.requirements}")
    print(f"💰 Budget: €{b2b_request.budget_limit}")
    print("-" * 60)
    
    try:
        # Create proposal
        proposal = await director.create_team_proposal(b2b_request)
        
        print(f"\n✅ Proposal Generated Successfully!")
        print(f"👥 Team Size: {len(proposal.agents)} agents")
        print(f"💵 Total Cost: €{proposal.estimated_cost.get('total_estimated_cost', 0)}")
        print(f"\n📋 Team Composition:")
        
        for i, agent in enumerate(proposal.agents, 1):
            print(f"  {i}. {agent.role} ({agent.seniority})")
            print(f"     Name: {agent.name}")
            
        # Check for B2B-specific roles
        roles = [agent.role.lower() for agent in proposal.agents]
        b2b_indicators = ['business', 'research', 'email', 'sales', 'lead', 'crm']
        instagram_indicators = ['content creator', 'visual', 'social media', 'instagram']
        
        b2b_count = sum(1 for role in roles if any(ind in role for ind in b2b_indicators))
        instagram_count = sum(1 for role in roles if any(ind in role for ind in instagram_indicators))
        
        print(f"\n📊 Domain Analysis:")
        print(f"  B2B-focused agents: {b2b_count}/{len(proposal.agents)}")
        print(f"  Instagram/Social agents: {instagram_count}/{len(proposal.agents)}")
        
        if b2b_count >= instagram_count and b2b_count >= 3:
            print("\n✅ SUCCESS: Team is correctly B2B-focused!")
        else:
            print("\n❌ ISSUE: Team seems misaligned with B2B requirements")
            
        print(f"\n💭 Rationale: {proposal.rationale}")
        
    except Exception as e:
        print(f"\n❌ Error creating proposal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("DIRECTOR B2B DOMAIN DETECTION TEST")
    print("=" * 60)
    asyncio.run(test_b2b_proposal())