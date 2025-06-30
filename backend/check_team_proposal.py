#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the backend directory to Python path
sys.path.append('/Users/pelleri/Documents/ai-team-orchestrator/backend')

# Load environment variables
load_dotenv('/Users/pelleri/Documents/ai-team-orchestrator/backend/.env')

async def check_recent_team_proposals():
    """Check the most recent team proposals in the database"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials in .env file")
        return
        
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Get the most recent team proposals
        print("🔍 Fetching recent team proposals...")
        result = supabase.table("team_proposals")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(3)\
            .execute()
        
        if not result.data:
            print("❌ No team proposals found in database")
            return
            
        print(f"📊 Found {len(result.data)} recent team proposals\n")
        
        for i, proposal in enumerate(result.data, 1):
            print(f"--- PROPOSAL {i} ---")
            print(f"ID: {proposal.get('id')}")
            print(f"Workspace ID: {proposal.get('workspace_id')}")
            print(f"Status: {proposal.get('status')}")
            print(f"Created: {proposal.get('created_at')}")
            
            # Examine the proposal_data structure
            proposal_data = proposal.get('proposal_data', {})
            print(f"Proposal Data Keys: {list(proposal_data.keys())}")
            
            # Check if agents exist and their structure
            agents = proposal_data.get('agents', [])
            print(f"Number of agents: {len(agents)}")
            
            if agents:
                print("\n🤖 AGENT DETAILS:")
                for j, agent in enumerate(agents, 1):
                    print(f"  Agent {j}:")
                    print(f"    Keys: {list(agent.keys())}")
                    print(f"    Name: {agent.get('name', 'N/A')}")
                    print(f"    Role: {agent.get('role', 'N/A')}")
                    print(f"    Seniority: {agent.get('seniority', 'N/A')}")
                    
                    # Check personality traits
                    personality_traits = agent.get('personality_traits', [])
                    print(f"    Personality Traits Type: {type(personality_traits)}")
                    print(f"    Personality Traits: {personality_traits}")
                    
                    # Check skills
                    hard_skills = agent.get('hard_skills', [])
                    soft_skills = agent.get('soft_skills', [])
                    print(f"    Hard Skills Type: {type(hard_skills)}")
                    print(f"    Hard Skills: {hard_skills}")
                    print(f"    Soft Skills Type: {type(soft_skills)}")
                    print(f"    Soft Skills: {soft_skills}")
                    
                    # Check other fields
                    for key in ['description', 'rationale', 'responsibilities']:
                        value = agent.get(key)
                        if value:
                            print(f"    {key}: {value[:100]}..." if len(str(value)) > 100 else f"    {key}: {value}")
                    print()
            
            print("=" * 60)
            print()
            
    except Exception as e:
        print(f"❌ Error checking team proposals: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_recent_team_proposals())