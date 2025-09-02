#!/usr/bin/env python3

"""
Test the fixed director via the actual HTTP API to confirm the fix is working
"""

import asyncio
import httpx
import json

async def test_fixed_director_api():
    """Test the API with exactly the same structure that worked in debug"""
    
    # Same payload structure as our debug test that worked
    payload = {
        "workspace_id": "bd9f85a3-3dfd-40d8-86d4-9a361f89f6e0",  # Same workspace ID as debug test
        "workspace_goal": "Creare una strategia di lead generation B2B per acquisire 100 contatti qualificati di CMO e CTO in aziende SaaS con 50-200 dipendenti. Configurare HubSpot CRM, creare sequenze email personalizzate e gestire il nurturing dei lead.",
        "user_feedback": "",
        "budget_constraint": {
            "max_cost": 10000.0,
            "currency": "EUR"
        }
    }
    
    print("🔍 TESTING FIXED DIRECTOR VIA HTTP API")
    print("=" * 50)
    
    print(f"📤 Payload (same workspace ID as successful debug test):")
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
                team_count = len(response_data.get('team_members', []))
                estimated_cost = response_data.get('estimated_cost', 'N/A')
                
                print(f"✅ Success! Team members: {team_count}")
                print(f"💰 Estimated cost: {estimated_cost}")
                
                # Show all team members
                for i, member in enumerate(response_data.get('team_members', [])):
                    print(f"   Agent {i+1}: {member.get('role', 'Unknown')} ({member.get('seniority', 'unknown')})")
                
                expected_count = 6
                if team_count == expected_count:
                    print(f"\n🎉 PERFECT! Fix confirmed via HTTP API")
                    print(f"   Expected: {expected_count} agents")
                    print(f"   Got: {team_count} agents") 
                    print(f"   The estimated_monthly_cost fix is working!")
                else:
                    print(f"\n❌ Issue: Expected {expected_count} agents, got {team_count}")
                    
            else:
                print(f"❌ Error Response: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_director_api())