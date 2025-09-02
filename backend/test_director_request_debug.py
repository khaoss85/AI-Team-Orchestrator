#!/usr/bin/env python3

"""
Test the actual director API endpoint to debug budget parsing issue
"""

import asyncio
import httpx
import json

async def test_director_api_call():
    """Test the actual director API call to see what's happening"""
    
    # The exact payload that frontend sends based on the API logs
    payload = {
        "workspace_id": "8b82a793-5198-441e-9fec-8882d2d98534",
        "workspace_goal": "Creare una strategia di lead generation B2B per acquisire 100 contatti qualificati di CMO e CTO in aziende SaaS con 50-200 dipendenti. Configurare HubSpot CRM, creare sequenze email personalizzate e gestire il nurturing dei lead.",
        "user_feedback": "",
        "budget_constraint": {
            "max_cost": 10000.0,
            "currency": "EUR"
        }
    }
    
    print("🔍 TESTING ACTUAL DIRECTOR API CALL")
    print("=" * 50)
    
    print(f"📤 Payload being sent:")
    print(json.dumps(payload, indent=2, default=str))
    print()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/director/proposal",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Success! Team members: {len(response_data.get('team_members', []))}")
                print(f"💰 Estimated cost: {response_data.get('estimated_cost', 'N/A')}")
                
                # Check if we got 6 agents as expected for 10k budget
                team_count = len(response_data.get('team_members', []))
                expected_count = 6
                
                if team_count == expected_count:
                    print(f"✅ BUDGET PARSING SUCCESS: Got {team_count} agents for 10k EUR budget")
                else:
                    print(f"❌ BUDGET PARSING FAILED: Got {team_count} agents, expected {expected_count}")
                    print(f"   This suggests budget is falling back to default logic")
                
            else:
                print(f"❌ Error Response: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_director_api_call())