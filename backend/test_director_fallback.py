#!/usr/bin/env python3
"""
Test script to diagnose why Director is returning 3-agent fallback team
instead of the expected 6+ agents for an 11,000 EUR budget workspace.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_director_team_generation():
    """Test the Director's team generation logic directly."""
    
    # Import after path setup
    from ai_agents.director import DirectorAgent
    from models import DirectorTeamProposal
    
    # Create test proposal request with 11,000 EUR budget
    proposal_request = DirectorTeamProposal(
        workspace_id="0de74da8-d2a6-47c3-9f08-3824bf1604e0",
        requirements="Generare 50 contatti B2B nel settore SaaS, con 3 sequenze email personalizzate",
        budget_limit=11000.0
    )
    
    logger.info(f"Testing with budget: {proposal_request.budget_limit} EUR")
    logger.info(f"Expected team size: min(8, max(3, int({proposal_request.budget_limit} / 1500))) = {min(8, max(3, int(proposal_request.budget_limit / 1500)))}")
    
    # Create Director instance
    director = DirectorAgent()
    
    # Test fallback logic directly
    logger.info("\n=== Testing Fallback Logic ===")
    fallback_dict = director._create_fallback_dict(proposal_request)
    logger.info(f"Fallback team size: {len(fallback_dict['agents'])}")
    logger.info(f"Fallback total cost: {fallback_dict['estimated_cost']['total_estimated_cost']} EUR")
    
    # Test default agents creation
    logger.info("\n=== Testing Default Agents Creation ===")
    default_agents = director._create_default_agents(
        budget_constraint_data=proposal_request.budget_limit,
        project_goal=proposal_request.requirements
    )
    logger.info(f"Default agents created: {len(default_agents)}")
    for i, agent in enumerate(default_agents):
        logger.info(f"  Agent {i+1}: {agent['name']} ({agent['seniority']}) - {agent.get('estimated_monthly_cost', 'N/A')} EUR")
    
    # Now test the full proposal generation
    logger.info("\n=== Testing Full Proposal Generation ===")
    try:
        proposal = await director.create_team_proposal(proposal_request)
        logger.info(f"Full proposal team size: {len(proposal.agents)}")
        logger.info(f"Full proposal total cost: {proposal.estimated_cost.get('total_estimated_cost', 'N/A')} EUR")
        logger.info(f"Rationale: {proposal.rationale}")
        
        # Log each agent
        for agent in proposal.agents:
            logger.info(f"  - {agent.name} ({agent.seniority}) as {agent.role}")
            
    except Exception as e:
        logger.error(f"Full proposal generation failed: {e}", exc_info=True)
        
    # Check SDK availability
    try:
        from agents import Agent as OpenAIAgent
        logger.info("\n✅ SDK is available (agents module imported successfully)")
    except ImportError:
        logger.warning("\n❌ SDK is NOT available - this triggers fallback!")
        
    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        logger.info(f"✅ OPENAI_API_KEY is set (length: {len(api_key)})")
    else:
        logger.warning("❌ OPENAI_API_KEY is NOT set")

if __name__ == "__main__":
    asyncio.run(test_director_team_generation())