#!/usr/bin/env python3
"""
Debug script to identify why 10,000 EUR budget generates only 3 agents instead of 6+
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agents.director import DirectorAgent
from models import DirectorTeamProposal
import asyncio
import logging
import uuid

# Setup logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_team_generation():
    """Test team generation with different budget values"""
    
    director = DirectorAgent()
    
    # Test different budget scenarios
    test_budgets = [
        1000,   # Should generate 3 agents: min(8, max(3, int(1000/1500))) = min(8, max(3, 0)) = 3
        3000,   # Should generate 3 agents: min(8, max(3, int(3000/1500))) = min(8, max(3, 2)) = 3
        5000,   # Should generate 3 agents: min(8, max(3, int(5000/1500))) = min(8, max(3, 3)) = 3
        7500,   # Should generate 5 agents: min(8, max(3, int(7500/1500))) = min(8, max(3, 5)) = 5
        10000,  # Should generate 6 agents: min(8, max(3, int(10000/1500))) = min(8, max(3, 6)) = 6
        15000,  # Should generate 8 agents: min(8, max(3, int(15000/1500))) = min(8, max(3, 10)) = 8
    ]
    
    for budget in test_budgets:
        print(f"\n{'='*60}")
        print(f"TESTING BUDGET: {budget} EUR")
        print(f"{'='*60}")
        
        # Calculate expected team size
        expected_team_size = min(8, max(3, int(budget / 1500)))
        print(f"Expected team size: {expected_team_size} agents")
        
        # Create test proposal request
        proposal_request = DirectorTeamProposal(
            workspace_id=str(uuid.uuid4()),
            requirements="Create a B2B lead generation campaign targeting SaaS CTOs",
            budget_limit=budget,
            user_feedback=""
        )
        
        print(f"Proposal request budget_limit: {proposal_request.budget_limit}")
        
        # Test the budget calculation in director
        # Simulate the calculation from line 1202
        budget_amount = proposal_request.budget_limit or 5000
        max_team_for_performance = min(8, max(3, int(budget_amount / 1500)))
        print(f"Director calculation: budget_amount={budget_amount}, max_team_for_performance={max_team_for_performance}")
        
        # Test the fallback calculation from _create_default_agents (line 1733)
        current_budget = float(budget)
        optimal_team_size = min(8, max(3, int(current_budget / 1500)))
        print(f"Fallback calculation: current_budget={current_budget}, optimal_team_size={optimal_team_size}")
        
        # Test actual director method (this might be where the issue is)
        try:
            print("Testing actual _create_default_agents method...")
            default_agents = director._create_default_agents(budget, proposal_request.requirements)
            print(f"Actual generated agents count: {len(default_agents)}")
            print(f"Agent roles: {[agent.get('role', 'Unknown') for agent in default_agents]}")
            
            # Check if the issue is in the fallback logic being triggered
            print("\nChecking if fallback is being used...")
            
        except Exception as e:
            print(f"Error testing _create_default_agents: {e}")
        
        print(f"Result: Expected {expected_team_size}, calculations show {max_team_for_performance}")

if __name__ == "__main__":
    asyncio.run(debug_team_generation())