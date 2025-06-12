#!/usr/bin/env python3

import asyncio
import json
import uuid
from ai_agents.director import DirectorAgent, DirectorConfig

async def test_director_with_user_feedback():
    """Test director with user feedback requesting 5 agents and high budget"""
    
    # Valid UUIDs for testing
    project_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    
    print(f"Testing with:")
    print(f"Project ID: {project_id}")
    print(f"User ID: {user_id}")
    print(f"Workspace ID: {workspace_id}")
    
    director = DirectorAgent()
    
    # Test case 1: User feedback requesting 5 agents with high budget
    config = DirectorConfig(
        workspace_id=workspace_id,
        user_id=user_id,
        goal="Creazione e qualificazione di liste di prospect per campagne outbound di MailUp",
        budget_constraint={"max_amount": 10000},
        user_feedback="possiamo portare a 5 agenti? Ne abbiamo bisogno di almeno 5 per questo progetto"
    )
    
    print("\n=== Test Case 1: User requesting 5 agents with 10k budget ===")
    try:
        proposal = await director.create_team_proposal(config)
        
        print(f"Proposal generated successfully!")
        print(f"Team size: {len(proposal.agents)}")
        print(f"Total cost: {proposal.estimated_cost}")
        
        # Print agent details
        for i, agent in enumerate(proposal.agents, 1):
            print(f"Agent {i}: {agent.role} (level: {getattr(agent, 'seniority_level', getattr(agent, 'level', 'unknown'))})")
        
        # Verify expectations
        if len(proposal.agents) >= 5:
            print("✅ SUCCESS: Team size respects user feedback (5+ agents)")
        else:
            print(f"❌ ISSUE: Team size is {len(proposal.agents)}, expected 5+")
            
        # Extract cost from estimated_cost dict
        cost_value = proposal.estimated_cost.get('total_cost', 0) if isinstance(proposal.estimated_cost, dict) else 0
        if cost_value >= 5000:  # Should use more of the 10k budget
            print(f"✅ SUCCESS: Budget utilization improved ({cost_value} EUR)")
        else:
            print(f"❌ ISSUE: Budget underutilized ({cost_value} EUR from 10k budget)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Case 2: Lower budget to see scaling ===")
    # Test case 2: Lower budget
    config_low = DirectorConfig(
        workspace_id=str(uuid.uuid4()),
        user_id=user_id,
        goal="Small test project with limited budget",
        budget_constraint={"max_amount": 2000},
        user_feedback="vogliamo 3 agenti se possibile"
    )
    
    try:
        proposal_low = await director.create_team_proposal(config_low)
        
        print(f"Low budget proposal:")
        print(f"Team size: {len(proposal_low.agents)}")
        print(f"Total cost: {proposal_low.estimated_cost}")
        
        if len(proposal_low.agents) <= len(proposal.agents):
            print("✅ SUCCESS: Team size scales with budget")
        else:
            print("❌ ISSUE: Team size doesn't scale properly with budget")
            
    except Exception as e:
        print(f"❌ Error in low budget test: {e}")

if __name__ == "__main__":
    asyncio.run(test_director_with_user_feedback())