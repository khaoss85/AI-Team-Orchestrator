#!/usr/bin/env python3
"""
Test script to verify the director is correctly generating teams based on budget.
This tests that the 10,000 EUR budget generates more than 1 agent.
"""

import asyncio
import os
import sys
from uuid import uuid4
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, '/Users/pelleri/Documents/ai-team-orchestrator/backend')

from models import DirectorTeamProposal, BudgetConstraint
from ai_agents.director import DirectorAgent

async def test_director_team_generation():
    """Test that director generates appropriate team size for budget"""
    
    test_cases = [
        {
            "name": "10K EUR B2B Project",
            "budget": 10000,
            "goal": "Generate 100 qualified B2B contacts for outbound sales campaign targeting Italian SMEs in technology sector",
            "expected_min_agents": 4,
            "expected_max_agents": 8
        },
        {
            "name": "5K EUR Marketing Project", 
            "budget": 5000,
            "goal": "Create Instagram content strategy and editorial calendar for 3 months",
            "expected_min_agents": 3,
            "expected_max_agents": 5
        },
        {
            "name": "1K EUR Small Project",
            "budget": 1000,
            "goal": "Simple research task on competitors",
            "expected_min_agents": 1,
            "expected_max_agents": 2
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING DIRECTOR TEAM GENERATION WITH BUDGET AWARENESS")
    print("="*80)
    
    director = DirectorAgent()
    
    for test_case in test_cases:
        print(f"\n📋 Test Case: {test_case['name']}")
        print(f"   Budget: €{test_case['budget']:,}")
        print(f"   Goal: {test_case['goal'][:60]}...")
        
        # Create proposal request
        proposal_request = DirectorTeamProposal(
            workspace_id=uuid4(),
            workspace_goal=test_case['goal'],
            budget_limit=test_case['budget'],
            requirements=test_case['goal'],
            budget_constraint=BudgetConstraint(max_cost=test_case['budget'], currency="EUR")
        )
        
        try:
            # Test direct fallback logic first
            print(f"\n   🔄 Testing Fallback Logic:")
            fallback_dict = director._create_fallback_dict(proposal_request)
            fallback_agents = fallback_dict.get('agents', [])
            print(f"      Fallback generated {len(fallback_agents)} agents")
            
            if fallback_agents:
                print(f"      Roles: {[a['role'] for a in fallback_agents]}")
            
            # Verify fallback meets expectations
            if len(fallback_agents) < test_case['expected_min_agents']:
                print(f"      ❌ FAIL: Expected at least {test_case['expected_min_agents']} agents, got {len(fallback_agents)}")
            elif len(fallback_agents) > test_case['expected_max_agents']:
                print(f"      ⚠️  WARNING: Generated {len(fallback_agents)} agents, expected max {test_case['expected_max_agents']}")
            else:
                print(f"      ✅ PASS: Agent count within expected range [{test_case['expected_min_agents']}-{test_case['expected_max_agents']}]")
            
            # Test _create_default_agents directly
            print(f"\n   🔧 Testing _create_default_agents:")
            default_agents = director._create_default_agents(
                test_case['budget'], 
                test_case['goal']
            )
            print(f"      Generated {len(default_agents)} agents")
            
            # Show cost breakdown
            total_cost = sum(a.get('estimated_monthly_cost', 0) for a in default_agents)
            print(f"      Total monthly cost: €{total_cost:,}")
            print(f"      Budget utilization: {(total_cost/test_case['budget']*100):.1f}%")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    # Ensure we have OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some features may not work.")
    
    asyncio.run(test_director_team_generation())