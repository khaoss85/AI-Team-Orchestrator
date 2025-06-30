#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# Add the backend directory to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def trigger_team_proposal():
    """Trigger a team proposal creation for the existing workspace"""
    
    # Use the workspace ID we found earlier
    workspace_id = "d5bc07b1-9d53-47ed-a5b0-425179b97c40"
    
    # Prepare the request payload
    payload = {
        "workspace_id": workspace_id,
        "goal": "B2B Outbound Sales Lists - Create comprehensive lead generation and outbound sales tools with email automation, sales tracking dashboard, and CRM integration",
        "budget_constraint": {
            "max_budget": 5000,
            "currency": "EUR",
            "timeline": "4 weeks"
        },
        "user_id": "550e8400-e29b-41d4-a716-446655440000"  # Dummy user ID
    }
    
    try:
        print("🚀 Triggering team proposal creation...")
        print(f"📊 Workspace ID: {workspace_id}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        # Make request to local backend
        response = requests.post(
            "http://localhost:8000/director/proposal",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Team proposal created successfully!")
            print(f"📋 Proposal ID: {result.get('id')}")
            print(f"👥 Number of agents: {len(result.get('agents', []))}")
            
            # Examine first agent structure
            agents = result.get('agents', [])
            if agents:
                first_agent = agents[0]
                print("\n🤖 FIRST AGENT STRUCTURE:")
                print(f"Keys: {list(first_agent.keys())}")
                print(f"Name: {first_agent.get('name')}")
                print(f"Role: {first_agent.get('role')}")
                print(f"Seniority: {first_agent.get('seniority')}")
                
                # Check personality traits
                personality_traits = first_agent.get('personality_traits')
                print(f"Personality Traits Type: {type(personality_traits)}")
                print(f"Personality Traits: {personality_traits}")
                
                # Check skills
                hard_skills = first_agent.get('hard_skills')
                soft_skills = first_agent.get('soft_skills')
                print(f"Hard Skills Type: {type(hard_skills)}")
                print(f"Hard Skills: {hard_skills}")
                print(f"Soft Skills Type: {type(soft_skills)}")
                print(f"Soft Skills: {soft_skills}")
                
                print("\n📋 FULL FIRST AGENT DATA:")
                print(json.dumps(first_agent, indent=2))
                
        else:
            print(f"❌ Failed to create team proposal: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the backend server is running on port 8000")
        print("Run: python main.py in the backend directory")
    except Exception as e:
        print(f"❌ Error triggering team proposal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(trigger_team_proposal())