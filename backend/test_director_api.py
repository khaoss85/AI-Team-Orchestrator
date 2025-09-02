#!/usr/bin/env python3
"""
Test the actual director API endpoint to see if fallback is being triggered
"""
import requests
import json
import uuid

def test_director_proposal():
    """Test the director proposal API with 10,000 EUR budget"""
    
    # Use existing workspace with 10,000 EUR budget
    workspace_id = "410f2700-a882-4a3a-bcb9-7432044e209b"
    
    # Test proposal creation
    proposal_data = {
        "workspace_id": workspace_id,
        "requirements": "Create a comprehensive B2B lead generation campaign targeting SaaS CTOs and decision makers",
        "budget_limit": 10000.0,
        "user_feedback": "I want a large team with diverse skills to maximize results"
    }
    
    print("Testing Director Proposal API")
    print(f"Budget: {proposal_data['budget_limit']} EUR")
    print(f"Expected team size: 6 agents")
    print("-" * 60)
    
    try:
        # Call the director proposal endpoint
        response = requests.post(
            "http://localhost:8000/api/director/proposal", 
            json=proposal_data,
            timeout=120  # Allow for longer processing
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API Response Status: {response.status_code}")
            print(f"Team members count: {len(result.get('team_members', []))}")
            
            if 'team_members' in result:
                print("\nTeam composition:")
                for i, member in enumerate(result['team_members'], 1):
                    role = member.get('role', 'Unknown')
                    seniority = member.get('seniority', 'Unknown')
                    cost = member.get('estimated_monthly_cost', 0)
                    print(f"  {i}. {role} ({seniority}) - {cost} EUR/month")
            
            total_cost = result.get('estimated_cost', {}).get('total_estimated_cost', 0)
            print(f"\nTotal estimated cost: {total_cost} EUR")
            print(f"Budget utilization: {(total_cost/10000)*100:.1f}%")
            
            # Check if this looks like fallback data
            if len(result.get('team_members', [])) == 3:
                print("⚠️  WARNING: Only 3 agents generated - this might be fallback logic being triggered")
                if 'rationale' in result:
                    rationale = result.get('rationale', '')
                    if 'fallback' in rationale.lower():
                        print(f"🚨 FALLBACK DETECTED: {rationale}")
            elif len(result.get('team_members', [])) >= 6:
                print("✅ Correct team size generated")
            else:
                print(f"❓ Unexpected team size: {len(result.get('team_members', []))} agents")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  API request timed out - this might indicate LLM timeout causing fallback")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_director_proposal()