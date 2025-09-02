#!/usr/bin/env python3

"""
Quick test to debug budget_constraint parsing issue.
This will help us understand why budget_constraint is None in the logs.
"""

import json
from models import DirectorTeamProposal, BudgetConstraint
from uuid import UUID

def test_budget_constraint_parsing():
    """Test how DirectorTeamProposal parses budget_constraint"""
    
    # Simulate the exact payload that the frontend sends
    frontend_payload = {
        "workspace_id": "8b82a793-5198-441e-9fec-8882d2d98534",
        "workspace_goal": "Test goal",
        "user_feedback": "",
        "budget_constraint": {
            "max_cost": 10000.0,
            "currency": "EUR"
        }
    }
    
    print("🔍 TESTING BUDGET CONSTRAINT PARSING")
    print("=" * 50)
    
    print(f"📤 Frontend payload:")
    print(json.dumps(frontend_payload, indent=2))
    print()
    
    try:
        # Test BudgetConstraint model directly first
        print("1️⃣ Testing BudgetConstraint model directly:")
        budget_constraint = BudgetConstraint(**frontend_payload["budget_constraint"])
        print(f"✅ BudgetConstraint parsed successfully: {budget_constraint}")
        print(f"   max_cost: {budget_constraint.max_cost}")
        print(f"   currency: {budget_constraint.currency}")
        print()
        
        # Test DirectorTeamProposal parsing
        print("2️⃣ Testing DirectorTeamProposal parsing:")
        proposal = DirectorTeamProposal(**frontend_payload)
        
        print(f"✅ DirectorTeamProposal created successfully")
        print(f"   workspace_id: {proposal.workspace_id}")
        print(f"   budget_constraint: {proposal.budget_constraint}")
        print(f"   budget_limit: {proposal.budget_limit}")
        
        if proposal.budget_constraint:
            print(f"   budget_constraint.max_cost: {proposal.budget_constraint.max_cost}")
            print(f"   budget_constraint.currency: {proposal.budget_constraint.currency}")
        else:
            print("   ❌ budget_constraint is None!")
            
    except Exception as e:
        print(f"❌ Error parsing DirectorTeamProposal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_budget_constraint_parsing()