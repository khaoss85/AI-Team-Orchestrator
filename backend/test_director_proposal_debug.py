#!/usr/bin/env python3
"""
Debug Director proposal issue
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_director_proposal():
    workspace_id = "35241c49-6b11-487a-80d8-4583ea50f60c"
    
    # Test with minimal valid proposal
    proposal_data = {
        "workspace_id": workspace_id,
        "workspace_goal": "Raccogliere 500 contatti ICP (CMO/CTO di aziende SaaS europee) e suggerire almeno 3 sequenze email da impostare su Hubspot",
        "user_feedback": "Ho bisogno di contatti REALI con nomi veri, email verificate e aziende specifiche per campagne outbound B2B. Ogni contatto deve avere: nome completo, email aziendale, azienda, ruolo CMO/CTO, paese europeo.",
        "budget_constraint": {
            "max_cost": 100.0,
            "currency": "USD"
        }
    }
    
    print("🧠 Testing Director proposal with real workspace...")
    print(f"Workspace ID: {workspace_id}")
    print(f"Payload: {json.dumps(proposal_data, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/director/proposal", json=proposal_data)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 422:
            print("❌ Validation Error Details:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print(response.text)
        elif response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            print(f"Proposal ID: {result.get('proposal_id')}")
            print(f"Team members: {len(result.get('team_members', []))}")
        else:
            print(f"❌ Unexpected error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_director_proposal()